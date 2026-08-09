import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch


# database.py initializes itself at import time, so force that import onto a
# disposable database before importing either application module.
_IMPORT_TEMP_DIR = tempfile.TemporaryDirectory()
os.environ["DATABASE_FILE"] = os.path.join(_IMPORT_TEMP_DIR.name, "import.sqlite")
os.environ["ADMIN_PASSWORD"] = "ImportAdmin123"
os.environ["CREDENTIAL_ENCRYPTION_KEY"] = (
    "MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA="
)

import database  # noqa: E402
import email_service  # noqa: E402


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_file = os.path.join(self.temp_dir.name, "users.sqlite")
        self.database_file_patch = patch.object(
            database, "DATABASE_FILE", self.database_file
        )
        self.database_file_patch.start()
        self.admin_password_patch = patch.dict(
            os.environ, {"ADMIN_PASSWORD": "InitialAdmin123"}
        )
        self.admin_password_patch.start()
        database.init_db()
        database.create_admin_user()

    def tearDown(self):
        self.admin_password_patch.stop()
        self.database_file_patch.stop()
        self.temp_dir.cleanup()

    def test_connection_enables_foreign_keys_and_busy_timeout(self):
        connection = database.get_db_connection()
        try:
            self.assertEqual(1, connection.execute("PRAGMA foreign_keys").fetchone()[0])
            self.assertEqual(5000, connection.execute("PRAGMA busy_timeout").fetchone()[0])
        finally:
            connection.close()

    def test_plaintext_card_key_migration_preserves_redeemable_code(self):
        success, _, user_id = database.create_user(
            "carduser", "Password123", "card@example.com"
        )
        self.assertTrue(success)

        with closing(sqlite3.connect(self.database_file)) as connection, connection:
            connection.execute("DROP TABLE card_keys")
            connection.execute(
                '''CREATE TABLE card_keys (
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       code TEXT UNIQUE NOT NULL,
                       credits INTEGER NOT NULL,
                       is_used INTEGER DEFAULT 0,
                       used_by INTEGER,
                       used_at TIMESTAMP,
                       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                   )'''
            )
            connection.execute(
                "INSERT INTO card_keys (code, credits) VALUES (?, ?)",
                ("legacy-code-123", 9),
            )

        database.init_db()

        with closing(sqlite3.connect(self.database_file)) as connection:
            columns = {
                row[1] for row in connection.execute("PRAGMA table_info(card_keys)")
            }
            migrated = connection.execute(
                "SELECT code_hash, code_prefix, fast_hash FROM card_keys"
            ).fetchone()
        self.assertNotIn("code", columns)
        self.assertEqual("LEGA", migrated[1])
        self.assertIsNotNone(migrated[2])

        success, _, credits = database.use_card_key("legacy-code-123", user_id)
        self.assertTrue(success)
        self.assertEqual(13, credits)

    def test_legacy_model_pricing_is_rebuilt_and_accepts_upserts(self):
        with closing(sqlite3.connect(self.database_file)) as connection, connection:
            connection.execute("DROP TABLE model_pricing")
            connection.execute(
                '''CREATE TABLE model_pricing (
                       model_id TEXT NOT NULL,
                       resolution TEXT NOT NULL,
                       price INTEGER NOT NULL,
                       image_size TEXT,
                       credits INTEGER,
                       updated_at TIMESTAMP,
                       PRIMARY KEY (model_id, resolution)
                   )'''
            )
            connection.execute(
                '''INSERT INTO model_pricing
                   (model_id, resolution, price, image_size, credits, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                ("legacy-model", "1K", 3, "1K", 3, datetime.now().isoformat()),
            )

        database.init_db()

        with closing(sqlite3.connect(self.database_file)) as connection:
            columns = [
                row[1] for row in connection.execute("PRAGMA table_info(model_pricing)")
            ]
        self.assertEqual(
            ["model_id", "image_size", "credits", "updated_at"], columns
        )
        self.assertEqual(3, database.get_model_pricing()[("legacy-model", "1K")])

        success, _ = database.save_model_pricing(
            {("legacy-model", "1K"): 5, ("new-model", "4K"): 8}
        )
        self.assertTrue(success)
        self.assertEqual(5, database.get_model_pricing()[("legacy-model", "1K")])
        self.assertEqual(8, database.get_model_pricing()[("new-model", "4K")])

    def test_admin_password_environment_variable_rotates_existing_password(self):
        self.assertTrue(database.verify_user("admin", "InitialAdmin123")[0])

        with patch.dict(os.environ, {"ADMIN_PASSWORD": "RotatedAdmin456"}):
            database.create_admin_user()

        self.assertFalse(database.verify_user("admin", "InitialAdmin123")[0])
        self.assertTrue(database.verify_user("admin", "RotatedAdmin456")[0])

    def test_api_settings_are_encrypted_and_history_is_not_retained(self):
        self.assertTrue(database.save_api_settings(
            "google_ai",
            "first-plaintext-api-key",
            email_sender="sender@example.com",
            email_password="first-plaintext-email-password",
            smtp_server="smtp.example.com",
            smtp_port=465,
        )[0])

        with closing(sqlite3.connect(self.database_file)) as connection:
            first_row = connection.execute(
                "SELECT api_key, email_password FROM api_settings"
            ).fetchone()
        self.assertTrue(first_row[0].startswith(database.ENCRYPTED_CREDENTIAL_PREFIX))
        self.assertTrue(first_row[1].startswith(database.ENCRYPTED_CREDENTIAL_PREFIX))
        self.assertNotIn("first-plaintext", first_row[0] + first_row[1])
        self.assertEqual("first-plaintext-api-key", database.get_active_api_settings()["api_key"])

        self.assertTrue(database.save_api_settings(
            "google_ai", "second-plaintext-api-key"
        )[0])
        with closing(sqlite3.connect(self.database_file)) as connection:
            rows = connection.execute(
                "SELECT api_key, is_active FROM api_settings"
            ).fetchall()
        self.assertEqual(1, len(rows))
        self.assertEqual(1, rows[0][1])
        self.assertNotIn("second-plaintext", rows[0][0])
        self.assertEqual("second-plaintext-api-key", database.get_active_api_settings()["api_key"])

    def test_plaintext_api_settings_migration_encrypts_current_and_prunes_history(self):
        with closing(sqlite3.connect(self.database_file)) as connection, connection:
            connection.execute(
                '''INSERT INTO api_settings
                   (provider, api_key, is_active, updated_at)
                   VALUES ('google_ai', 'old-key', 0, '2026-01-01T00:00:00')'''
            )
            connection.execute(
                '''INSERT INTO api_settings
                   (provider, api_key, email_password, is_active, updated_at)
                   VALUES ('google_ai', 'current-key', 'smtp-secret', 1,
                           '2026-01-02T00:00:00')'''
            )

        self.assertTrue(database.migrate_api_settings_credentials())

        with closing(sqlite3.connect(self.database_file)) as connection:
            rows = connection.execute(
                "SELECT api_key, email_password, is_active FROM api_settings"
            ).fetchall()
        self.assertEqual(1, len(rows))
        self.assertTrue(rows[0][0].startswith(database.ENCRYPTED_CREDENTIAL_PREFIX))
        self.assertTrue(rows[0][1].startswith(database.ENCRYPTED_CREDENTIAL_PREFIX))
        self.assertEqual(1, rows[0][2])
        settings = database.get_active_api_settings()
        self.assertEqual("current-key", settings["api_key"])
        self.assertEqual("smtp-secret", settings["email_password"])

    def test_database_credential_save_requires_encryption_key(self):
        with patch.dict(os.environ, {"CREDENTIAL_ENCRYPTION_KEY": ""}):
            success, message = database.save_api_settings("google_ai", "api-key")
        self.assertFalse(success)
        self.assertIn("CREDENTIAL_ENCRYPTION_KEY", message)

    def test_credential_key_accepts_missing_base64_padding(self):
        canonical_key = "MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA="
        with patch.dict(
            os.environ,
            {"CREDENTIAL_ENCRYPTION_KEY": canonical_key.removesuffix("=")},
        ):
            cipher = database._get_credential_fernet(required=True)
            token = cipher.encrypt(b"credential")
            self.assertEqual(b"credential", cipher.decrypt(token))

    def test_credential_key_still_rejects_invalid_values(self):
        with patch.dict(os.environ, {"CREDENTIAL_ENCRYPTION_KEY": "not-a-key"}):
            with self.assertRaises(database.CredentialEncryptionError):
                database._get_credential_fernet(required=True)

    def test_delete_user_rejects_missing_and_admin_users(self):
        self.assertFalse(database.delete_user(987654)[0])
        admin = database.verify_user("admin", "InitialAdmin123")[2]
        self.assertFalse(database.delete_user(admin["id"])[0])

    def test_delete_user_with_card_history_clears_foreign_key(self):
        success, _, user_id = database.create_user(
            "deleteuser", "Password123", "delete@example.com"
        )
        self.assertTrue(success)
        success, _, keys = database.generate_card_keys(2, 1)
        self.assertTrue(success)
        self.assertTrue(database.use_card_key(keys[0]["code"], user_id)[0])
        self.assertTrue(
            database.reserve_generation_credits(
                user_id,
                1,
                "charge-delete-cascade",
                (datetime.now() + timedelta(minutes=10)).isoformat(),
            )[0]
        )

        self.assertTrue(database.delete_user(user_id)[0])
        with closing(sqlite3.connect(self.database_file)) as connection:
            used_by = connection.execute(
                "SELECT used_by FROM card_keys WHERE id = 1"
            ).fetchone()[0]
            charge_count = connection.execute(
                '''SELECT COUNT(*) FROM generation_charges
                   WHERE charge_id = 'charge-delete-cascade' '''
            ).fetchone()[0]
        self.assertIsNone(used_by)
        self.assertEqual(0, charge_count)

    def test_generation_credit_reservation_is_atomic(self):
        success, _, user_id = database.create_user(
            "chargeuser", "Password123", "charge@example.com"
        )
        self.assertTrue(success)
        expires_at = (datetime.now() + timedelta(minutes=10)).isoformat()

        success, _, remaining = database.reserve_generation_credits(
            user_id, 3, "charge-reserve-1", expires_at
        )
        self.assertTrue(success)
        self.assertEqual(1, remaining)

        success, _, remaining = database.reserve_generation_credits(
            user_id, 2, "charge-reserve-2", expires_at
        )
        self.assertFalse(success)
        self.assertEqual(1, remaining)
        success, _, remaining = database.reserve_generation_credits(
            987654, 1, "charge-missing-user", expires_at
        )
        self.assertFalse(success)
        self.assertEqual(0, remaining)

        with closing(sqlite3.connect(self.database_file)) as connection:
            charges = connection.execute(
                "SELECT charge_id, credits, status FROM generation_charges"
            ).fetchall()
            indexes = {
                row[1]
                for row in connection.execute(
                    "PRAGMA index_list(generation_charges)"
                ).fetchall()
            }
        self.assertEqual([("charge-reserve-1", 3, "pending")], charges)
        self.assertIn("idx_generation_charges_pending", indexes)
        self.assertIn("idx_generation_charges_expires", indexes)

    def test_generation_charge_refund_is_idempotent(self):
        success, _, user_id = database.create_user(
            "refunduser", "Password123", "refund@example.com"
        )
        self.assertTrue(success)
        expires_at = (datetime.now() + timedelta(minutes=10)).isoformat()
        self.assertTrue(
            database.reserve_generation_credits(
                user_id, 2, "charge-refund", expires_at
            )[0]
        )

        self.assertTrue(
            database.resolve_generation_charge("charge-refund", refund=True)[0]
        )
        self.assertTrue(
            database.resolve_generation_charge("charge-refund", refund=True)[0]
        )
        self.assertFalse(
            database.resolve_generation_charge("charge-refund", refund=False)[0]
        )

        with closing(sqlite3.connect(self.database_file)) as connection:
            credits = connection.execute(
                "SELECT credits FROM users WHERE id = ?", (user_id,)
            ).fetchone()[0]
            charge = connection.execute(
                '''SELECT status, resolved_at FROM generation_charges
                   WHERE charge_id = 'charge-refund' '''
            ).fetchone()
        self.assertEqual(4, credits)
        self.assertEqual("refunded", charge[0])
        self.assertIsNotNone(charge[1])

    def test_generation_charge_commit_is_idempotent(self):
        success, _, user_id = database.create_user(
            "commituser", "Password123", "commit@example.com"
        )
        self.assertTrue(success)
        expires_at = (datetime.now() + timedelta(minutes=10)).isoformat()
        self.assertTrue(
            database.reserve_generation_credits(
                user_id, 2, "charge-commit", expires_at
            )[0]
        )

        self.assertTrue(
            database.resolve_generation_charge("charge-commit", refund=False)[0]
        )
        self.assertTrue(
            database.resolve_generation_charge("charge-commit", refund=False)[0]
        )
        self.assertFalse(
            database.resolve_generation_charge("charge-commit", refund=True)[0]
        )

        with closing(sqlite3.connect(self.database_file)) as connection:
            credits = connection.execute(
                "SELECT credits FROM users WHERE id = ?", (user_id,)
            ).fetchone()[0]
            status = connection.execute(
                '''SELECT status FROM generation_charges
                   WHERE charge_id = 'charge-commit' '''
            ).fetchone()[0]
        self.assertEqual(2, credits)
        self.assertEqual("committed", status)

    def test_stale_generation_charge_query_only_returns_expired_pending(self):
        success, _, user_id = database.create_user(
            "staleuser", "Password123", "stale@example.com"
        )
        self.assertTrue(success)
        now = datetime.now()
        old_expiry = (now - timedelta(minutes=1)).isoformat()
        future_expiry = (now + timedelta(minutes=10)).isoformat()
        self.assertTrue(
            database.reserve_generation_credits(
                user_id, 1, "charge-old", old_expiry
            )[0]
        )
        self.assertTrue(
            database.reserve_generation_credits(
                user_id, 1, "charge-future", future_expiry
            )[0]
        )
        self.assertTrue(
            database.reserve_generation_credits(
                user_id, 1, "charge-resolved", old_expiry
            )[0]
        )
        self.assertTrue(
            database.resolve_generation_charge("charge-resolved", refund=False)[0]
        )

        stale = database.get_stale_generation_charges(now.isoformat())
        self.assertEqual(["charge-old"], [charge["charge_id"] for charge in stale])
        self.assertEqual("pending", stale[0]["status"])

    def test_atomic_registration_does_not_consume_code_on_insert_failure(self):
        database.create_user("takenuser", "Password123", "taken@example.com")
        email = "new@example.com"
        code = "123456"
        code_hash = database.generate_password_hash(code)
        database.create_verification_code(
            email, code_hash, (datetime.now() + timedelta(minutes=10)).isoformat()
        )

        success, _, _ = database.register_user_with_verification_code(
            "takenuser", "Password123", email, code
        )
        self.assertFalse(success)
        with closing(sqlite3.connect(self.database_file)) as connection:
            used = connection.execute(
                "SELECT used FROM verification_codes WHERE code_hash = ?", (code_hash,)
            ).fetchone()[0]
        self.assertEqual(0, used)

        success, _, user_id = database.register_user_with_verification_code(
            "newuser", "Password123", email, code
        )
        self.assertTrue(success)
        self.assertIsNotNone(user_id)
        self.assertFalse(
            database.register_user_with_verification_code(
                "anotheruser", "Password123", email, code
            )[0]
        )

    def test_invalid_registration_and_email_failure_cleanup_keep_codes_usable(self):
        email = "cleanup@example.com"
        code = "654321"
        code_hash = database.generate_password_hash(code)
        database.create_verification_code(
            email, code_hash, (datetime.now() + timedelta(minutes=10)).isoformat()
        )

        self.assertFalse(
            database.register_user_with_verification_code(
                "x", "Password123", email, code
            )[0]
        )
        self.assertTrue(database.verify_email_code(email, code)[0])

        other_hash = database.generate_password_hash("111111")
        database.create_verification_code(
            email, other_hash, (datetime.now() + timedelta(minutes=10)).isoformat()
        )
        self.assertTrue(database.delete_verification_code(email, other_hash))
        self.assertFalse(database.delete_verification_code(email, other_hash))


class EmailServiceTests(unittest.TestCase):
    def test_smtp_fields_fall_back_individually_and_use_timeout(self):
        smtp_context = MagicMock()
        smtp_server = smtp_context.return_value.__enter__.return_value
        settings = {
            "email_sender": "database@example.com",
            "email_password": None,
            "smtp_server": "",
            "smtp_port": 2465,
        }
        environment = {
            "EMAIL_SENDER": "environment@example.com",
            "EMAIL_PASSWORD": "environment-password",
            "SMTP_SERVER": "smtp.environment.test",
            "SMTP_PORT": "9999",
            "SMTP_TIMEOUT": "7.5",
        }

        with patch.object(email_service, "get_active_api_settings", return_value=settings), \
                patch.object(email_service.smtplib, "SMTP_SSL", smtp_context), \
                patch.dict(os.environ, environment, clear=False):
            success, message = email_service.send_verification_email(
                "recipient@example.com", "123456"
            )

        self.assertTrue(success)
        self.assertEqual("success", message)
        smtp_context.assert_called_once_with(
            "smtp.environment.test", 2465, timeout=7.5
        )
        smtp_server.login.assert_called_once_with(
            "database@example.com", "environment-password"
        )
        smtp_server.send_message.assert_called_once()


if __name__ == "__main__":
    unittest.main()
