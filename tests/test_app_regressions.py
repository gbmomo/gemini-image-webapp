import base64
import io
import os
import re
import tempfile
import unittest
import uuid
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image


_IMPORT_TEMP_DIR = tempfile.TemporaryDirectory()
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ["DISABLE_BACKGROUND_TASKS"] = "true"
os.environ["DATABASE_FILE"] = os.path.join(_IMPORT_TEMP_DIR.name, "import.sqlite")
os.environ["DATA_DIR"] = os.path.join(_IMPORT_TEMP_DIR.name, "data")
os.environ["IMAGES_DIR"] = os.path.join(_IMPORT_TEMP_DIR.name, "images")
os.environ["THUMBNAILS_DIR"] = os.path.join(_IMPORT_TEMP_DIR.name, "thumbnails")

import app as app_module  # noqa: E402
import database  # noqa: E402


class AppRegressionTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_file_patch = patch.object(
            database, "DATABASE_FILE", os.path.join(self.temp_dir.name, "users.sqlite")
        )
        self.database_file_patch.start()
        self.path_patches = [
            patch.object(app_module, "DATA_DIR", os.path.join(self.temp_dir.name, "data")),
            patch.object(app_module, "SESSIONS_DIR", os.path.join(self.temp_dir.name, "sessions")),
            patch.object(app_module, "IMAGES_DIR", os.path.join(self.temp_dir.name, "images")),
            patch.object(app_module, "THUMBNAILS_DIR", os.path.join(self.temp_dir.name, "thumbnails")),
            patch.object(
                app_module,
                "MAINTENANCE_LOCK_FILE",
                os.path.join(self.temp_dir.name, "maintenance.lock"),
            ),
        ]
        for path_patch in self.path_patches:
            path_patch.start()
        for directory in (
            app_module.DATA_DIR,
            app_module.SESSIONS_DIR,
            app_module.IMAGES_DIR,
            app_module.THUMBNAILS_DIR,
        ):
            os.makedirs(directory, exist_ok=True)

        self.admin_password_patch = patch.dict(
            os.environ, {"ADMIN_PASSWORD": "AdminPassword123"}
        )
        self.admin_password_patch.start()
        database.init_db()
        database.create_admin_user()
        success, _, self.user_id = database.create_user(
            "regular-user", "Password123", "regular@example.com"
        )
        self.assertTrue(success)
        self.admin_id = next(
            user["id"] for user in database.get_all_users() if user["username"] == "admin"
        )

        self.previous_csrf_setting = app_module.app.config.get("WTF_CSRF_ENABLED", True)
        app_module.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
        with app_module.active_chats_lock:
            app_module.active_chats.clear()

    def tearDown(self):
        app_module.app.config["WTF_CSRF_ENABLED"] = self.previous_csrf_setting
        self.admin_password_patch.stop()
        for path_patch in reversed(self.path_patches):
            path_patch.stop()
        self.database_file_patch.stop()
        self.temp_dir.cleanup()

    def _client_for(self, user_id):
        client = app_module.app.test_client()
        user = database.get_user_by_id(user_id)
        with client.session_transaction() as flask_session:
            flask_session["user_id"] = user_id
            flask_session["username"] = user["username"]
            flask_session["is_admin"] = user["is_admin"]
        return client

    def _create_session(self, user_id):
        session_id = str(uuid.uuid4())
        now = "2026-08-03T12:00:00"
        app_module.save_sessions(user_id, {
            session_id: {
                "title": "新对话",
                "created_at": now,
                "updated_at": now,
                "messages": [],
                "settings": None,
            }
        })
        return session_id

    def _generate_payload(self, session_id, **overrides):
        payload = {
            "session_id": session_id,
            "prompt": "test image",
            "model": "gemini-2.5-flash-image",
            "image_size": "1K",
            "aspect_ratio": "1:1",
            "reference_images": [],
        }
        payload.update(overrides)
        return payload

    def test_text_only_generation_refunds_reserved_credits(self):
        session_id = self._create_session(self.user_id)
        response_part = SimpleNamespace(
            text="I cannot create that image", inline_data=None, thought_signature=None
        )
        fake_chat = SimpleNamespace(
            send_message=lambda contents: SimpleNamespace(parts=[response_part])
        )
        client = self._client_for(self.user_id)

        with patch.object(app_module, "ensure_client_current", return_value=True), patch.object(
            app_module, "get_or_create_chat", return_value=fake_chat
        ):
            response = client.post(
                "/api/generate", json=self._generate_payload(session_id)
            )

        self.assertEqual(422, response.status_code)
        self.assertEqual(4, database.get_user_by_id(self.user_id)["credits"])
        self.assertEqual([], app_module.load_sessions(self.user_id)[session_id]["messages"])

    def test_response_processing_failure_removes_partially_written_files(self):
        class BrokenPart:
            @property
            def text(self):
                raise RuntimeError("broken response part")

        image_part = SimpleNamespace(
            text=None,
            inline_data=object(),
            thought_signature=None,
            as_image=lambda: Image.new("RGB", (2, 2), "blue"),
        )
        response = SimpleNamespace(parts=[image_part, BrokenPart()])

        with self.assertRaises(RuntimeError):
            app_module._process_gemini_response(response, str(uuid.uuid4()))

        self.assertEqual([], os.listdir(app_module.IMAGES_DIR))
        self.assertEqual([], os.listdir(app_module.THUMBNAILS_DIR))

    def test_refund_database_error_does_not_escape_cleanup_path(self):
        session_id = str(uuid.uuid4())
        image_filename = "failed-generation.png"
        image_path = os.path.join(app_module.IMAGES_DIR, image_filename)
        with open(image_path, "wb") as image_file:
            image_file.write(b"image")
        with app_module.active_chats_lock:
            app_module.active_chats[session_id] = {"chat": object()}

        with patch.object(
            app_module, "resolve_generation_charge", side_effect=RuntimeError("database busy")
        ):
            app_module._handle_generation_failure(
                "charge-id",
                {"image": f"/static/images/{image_filename}", "thumbnail": None},
                [],
                session_id,
                False,
            )

        self.assertFalse(os.path.exists(image_path))
        with app_module.active_chats_lock:
            self.assertNotIn(session_id, app_module.active_chats)

    def test_stale_generation_charges_reconcile_from_session_evidence(self):
        expired_at = (datetime.now() - timedelta(seconds=1)).isoformat()
        self.assertTrue(
            database.reserve_generation_credits(
                self.user_id, 1, "charge-without-output", expired_at
            )[0]
        )
        self.assertEqual(1, app_module.reconcile_stale_generation_charges())
        self.assertEqual(4, database.get_user_by_id(self.user_id)["credits"])

        session_id = self._create_session(self.user_id)
        self.assertTrue(
            database.reserve_generation_credits(
                self.user_id, 1, "charge-with-output", expired_at
            )[0]
        )
        sessions = app_module.load_sessions(self.user_id)
        sessions[session_id]["messages"].append({
            "role": "assistant",
            "image": "/static/images/completed.png",
            "generation_charge_id": "charge-with-output",
        })
        app_module.save_sessions(self.user_id, sessions)

        self.assertEqual(1, app_module.reconcile_stale_generation_charges())
        self.assertEqual(3, database.get_user_by_id(self.user_id)["credits"])
        with database.get_db() as connection:
            statuses = dict(connection.execute(
                "SELECT charge_id, status FROM generation_charges"
            ).fetchall())
        self.assertEqual("refunded", statuses["charge-without-output"])
        self.assertEqual("committed", statuses["charge-with-output"])

    def test_successful_generation_persists_real_reference_extension(self):
        session_id = self._create_session(self.user_id)
        reference_buffer = io.BytesIO()
        Image.new("RGB", (2, 2), "white").save(reference_buffer, format="JPEG")
        encoded_reference = base64.b64encode(reference_buffer.getvalue()).decode("ascii")
        generated_image = Image.new("RGB", (2, 2), "blue")
        response_part = SimpleNamespace(
            text=None,
            inline_data=object(),
            thought_signature=None,
            as_image=lambda: generated_image,
        )
        fake_chat = SimpleNamespace(
            send_message=lambda contents: SimpleNamespace(parts=[response_part])
        )
        client = self._client_for(self.user_id)

        with patch.object(app_module, "ensure_client_current", return_value=True), patch.object(
            app_module, "get_or_create_chat", return_value=fake_chat
        ):
            response = client.post(
                "/api/generate",
                json=self._generate_payload(
                    session_id,
                    reference_images=[f"data:image/jpeg;base64,{encoded_reference}"],
                ),
            )

        self.assertEqual(200, response.status_code)
        payload = response.get_json()
        self.assertEqual(3, database.get_user_by_id(self.user_id)["credits"])
        self.assertEqual(1, len(payload["reference_images"]))
        reference_filename = payload["reference_images"][0]
        self.assertTrue(reference_filename.endswith(".jpg"))
        with open(os.path.join(app_module.IMAGES_DIR, reference_filename), "rb") as image_file:
            self.assertEqual(b"\xff\xd8", image_file.read(2))
        messages = app_module.load_sessions(self.user_id)[session_id]["messages"]
        self.assertEqual([reference_filename], messages[0]["reference_images"])
        self.assertEqual(payload["image"], messages[1]["image"])
        self.assertIn("generation_charge_id", messages[1])
        public_messages = client.get(f"/api/sessions/{session_id}").get_json()["messages"]
        self.assertNotIn("generation_charge_id", public_messages[1])

    def test_invalid_reference_image_is_rejected_before_charging(self):
        session_id = self._create_session(self.user_id)
        client = self._client_for(self.user_id)
        with patch.object(app_module, "ensure_client_current", return_value=True):
            response = client.post(
                "/api/generate",
                json=self._generate_payload(
                    session_id,
                    reference_images=["data:image/png;base64,bm90LWEtcmVhbC1pbWFnZQ=="],
                ),
            )

        self.assertEqual(400, response.status_code)
        self.assertEqual(4, database.get_user_by_id(self.user_id)["credits"])

    def test_admin_delete_rejection_preserves_admin_history_and_image(self):
        session_id = self._create_session(self.admin_id)
        image_path = os.path.join(app_module.IMAGES_DIR, "admin-owned.png")
        with open(image_path, "wb") as image_file:
            image_file.write(b"image")
        sessions = app_module.load_sessions(self.admin_id)
        sessions[session_id]["messages"] = [
            {"role": "assistant", "image": "/static/images/admin-owned.png"}
        ]
        app_module.save_sessions(self.admin_id, sessions)

        response = self._client_for(self.admin_id).delete(
            f"/api/admin/users/{self.admin_id}"
        )

        self.assertEqual(400, response.status_code)
        self.assertTrue(os.path.exists(app_module.get_user_sessions_file(self.admin_id)))
        self.assertTrue(os.path.exists(image_path))

    def test_media_requires_owner_or_admin(self):
        session_id = self._create_session(self.user_id)
        filename = "owned.png"
        with open(os.path.join(app_module.IMAGES_DIR, filename), "wb") as image_file:
            image_file.write(b"image")
        sessions = app_module.load_sessions(self.user_id)
        sessions[session_id]["messages"] = [
            {"role": "assistant", "image": f"/static/images/{filename}"}
        ]
        app_module.save_sessions(self.user_id, sessions)

        owner_response = self._client_for(self.user_id).get(f"/static/images/{filename}")
        anonymous_response = app_module.app.test_client().get(f"/static/images/{filename}")
        bypass_response = app_module.app.test_client().get(
            f"/static/images/../images/{filename}"
        )
        public_asset_response = app_module.app.test_client().get("/static/css/style.css")
        success, _, other_user_id = database.create_user(
            "other-user", "Password123", "other@example.com"
        )
        self.assertTrue(success)
        other_response = self._client_for(other_user_id).get(f"/static/images/{filename}")
        admin_response = self._client_for(self.admin_id).get(f"/static/images/{filename}")
        statuses = [
            owner_response.status_code,
            anonymous_response.status_code,
            bypass_response.status_code,
            public_asset_response.status_code,
            other_response.status_code,
            admin_response.status_code,
        ]
        for response in (
            owner_response,
            anonymous_response,
            bypass_response,
            public_asset_response,
            other_response,
            admin_response,
        ):
            response.close()

        self.assertEqual([200, 302, 404, 200, 403, 200], statuses)

    def test_unsafe_api_requests_require_valid_csrf_token(self):
        app_module.app.config["WTF_CSRF_ENABLED"] = True
        client = self._client_for(self.user_id)
        page = client.get("/")
        self.addCleanup(page.close)
        token_match = re.search(
            r'<meta name="csrf-token" content="([^"]+)">',
            page.get_data(as_text=True),
        )
        self.assertIsNotNone(token_match)

        rejected = client.post("/api/sessions")
        accepted = client.post(
            "/api/sessions",
            headers={"X-CSRFToken": token_match.group(1)},
        )
        self.addCleanup(rejected.close)
        self.addCleanup(accepted.close)

        self.assertEqual(400, rejected.status_code)
        self.assertEqual(200, accepted.status_code)

    def test_anonymous_session_probe_does_not_invalidate_login_csrf(self):
        app_module.app.config["WTF_CSRF_ENABLED"] = True
        client = app_module.app.test_client()
        page = client.get("/")
        token_match = re.search(
            r'<meta name="csrf-token" content="([^"]+)">',
            page.get_data(as_text=True),
        )
        self.assertIsNotNone(token_match)
        with client.session_transaction() as flask_session:
            session_csrf_token = flask_session.get("csrf_token")
        self.assertIsNotNone(session_csrf_token)

        unauthorized = client.get("/api/sessions")
        self.assertEqual(401, unauthorized.status_code)
        with client.session_transaction() as flask_session:
            self.assertEqual(session_csrf_token, flask_session.get("csrf_token"))

        login = client.post(
            "/api/login",
            headers={"X-CSRFToken": token_match.group(1)},
            json={"username": "admin", "password": "AdminPassword123"},
        )
        self.assertEqual(200, login.status_code)
        self.assertTrue(login.get_json()["success"])


if __name__ == "__main__":
    unittest.main()
