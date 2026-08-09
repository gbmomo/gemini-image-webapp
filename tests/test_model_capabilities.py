import os
import tempfile
import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import patch


_TEST_TEMP_DIR = tempfile.TemporaryDirectory()
os.environ.setdefault("SECRET_KEY", "test-only-secret-key-with-at-least-32-bytes")
os.environ.setdefault(
    "CREDENTIAL_ENCRYPTION_KEY",
    "MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA=",
)
os.environ["DISABLE_BACKGROUND_TASKS"] = "true"
os.environ.setdefault("DATABASE_FILE", os.path.join(_TEST_TEMP_DIR.name, "users.sqlite"))
os.environ["DATA_DIR"] = os.path.join(_TEST_TEMP_DIR.name, "data")
os.environ["IMAGES_DIR"] = os.path.join(_TEST_TEMP_DIR.name, "images")
os.environ["THUMBNAILS_DIR"] = os.path.join(_TEST_TEMP_DIR.name, "thumbnails")

import app as app_module


EXPECTED_CAPABILITIES = {
    "gemini-3.1-flash-lite-image": {
        "sizes": ["1K"],
        "ratios": ["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"],
        "thinking_levels": ["minimal", "high"],
    },
    "gemini-3.1-flash-image": {
        "sizes": ["512", "1K", "2K", "4K"],
        "ratios": ["1:1", "1:4", "1:8", "2:3", "3:2", "3:4", "4:1", "4:3", "4:5", "5:4", "8:1", "9:16", "16:9", "21:9"],
        "thinking_levels": ["minimal", "high"],
    },
    "gemini-3-pro-image": {
        "sizes": ["1K", "2K", "4K"],
        "ratios": ["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"],
        "thinking_levels": [],
    },
    "gemini-2.5-flash-image": {
        "sizes": ["1K"],
        "ratios": ["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"],
        "thinking_levels": [],
    },
}


class ModelCapabilityTests(unittest.TestCase):
    def test_capability_matrix_matches_official_documentation(self):
        actual = {
            model_id: {
                "sizes": config["sizes"],
                "ratios": config["ratios"],
                "thinking_levels": config["thinking_levels"],
            }
            for model_id, config in app_module.MODEL_CAPABILITIES.items()
        }
        self.assertEqual(EXPECTED_CAPABILITIES, actual)

    def test_models_endpoint_exposes_only_supported_options(self):
        with patch.object(app_module, "get_model_pricing", return_value={}):
            response = app_module.app.test_client().get("/api/models")

        self.assertEqual(200, response.status_code)
        payload = response.get_json()
        models = {model["id"]: model for model in payload["models"]}
        for model_id, expected in EXPECTED_CAPABILITIES.items():
            self.assertEqual(expected["sizes"], [size["id"] for size in models[model_id]["sizes"]])
            self.assertEqual(expected["ratios"], models[model_id]["ratios"])
            self.assertEqual(expected["thinking_levels"], models[model_id]["thinking_levels"])
            expected_default = "minimal" if expected["thinking_levels"] else None
            self.assertEqual(expected_default, models[model_id]["default_thinking_level"])

    def test_generate_validation_rejects_cross_model_options(self):
        payload = {
            "session_id": str(uuid.uuid4()),
            "prompt": "test",
            "model": "gemini-2.5-flash-image",
            "image_size": "4K",
            "aspect_ratio": "1:1",
            "reference_images": [],
        }
        with app_module.app.test_request_context(json=payload):
            response, status = app_module._validate_generate_params(payload)
        self.assertEqual(400, status)
        self.assertIn("不支持", response.get_json()["error"])

        payload.update(image_size="1K", aspect_ratio="1:8")
        with app_module.app.test_request_context(json=payload):
            response, status = app_module._validate_generate_params(payload)
        self.assertEqual(400, status)
        self.assertIn("不支持", response.get_json()["error"])

    def test_generate_validation_accepts_every_documented_combination(self):
        for model_id, capability in EXPECTED_CAPABILITIES.items():
            for image_size in capability["sizes"]:
                for aspect_ratio in capability["ratios"]:
                    payload = {
                        "session_id": str(uuid.uuid4()),
                        "prompt": "test",
                        "model": model_id,
                        "image_size": image_size,
                        "aspect_ratio": aspect_ratio,
                        "reference_images": [],
                    }
                    with app_module.app.test_request_context(json=payload):
                        self.assertIsNone(app_module._validate_generate_params(payload))

    def test_chat_uses_generate_content_image_config(self):
        calls = []

        class FakeChats:
            def create(self, **kwargs):
                calls.append(kwargs)
                return "chat"

        session_id = str(uuid.uuid4())
        fake_client = SimpleNamespace(chats=FakeChats())
        try:
            with patch.object(app_module, "client", fake_client):
                chat = app_module.create_chat(
                    session_id,
                    aspect_ratio="16:9",
                    image_size="2K",
                    model="gemini-3.1-flash-image",
                )
        finally:
            with app_module.active_chats_lock:
                app_module.active_chats.pop(session_id, None)

        self.assertEqual("chat", chat)
        config = calls[0]["config"]
        self.assertEqual("16:9", config.image_config.aspect_ratio)
        self.assertEqual("2K", config.image_config.image_size)
        self.assertFalse(hasattr(config, "response_format"))

    def test_thinking_level_validation_is_model_scoped(self):
        base_payload = {
            "session_id": str(uuid.uuid4()),
            "prompt": "test",
            "image_size": "1K",
            "aspect_ratio": "1:1",
            "reference_images": [],
        }
        for model in ("gemini-3.1-flash-image", "gemini-3.1-flash-lite-image"):
            for level in ("minimal", "high"):
                payload = {**base_payload, "model": model, "thinking_level": level}
                with app_module.app.test_request_context(json=payload):
                    self.assertIsNone(app_module._validate_generate_params(payload))

        invalid_payloads = [
            {**base_payload, "model": "gemini-3.1-flash-image", "thinking_level": "medium"},
            {**base_payload, "model": "gemini-3.1-flash-image", "thinking_level": 1},
            {**base_payload, "model": "gemini-3-pro-image", "thinking_level": "high"},
            {**base_payload, "model": "gemini-2.5-flash-image", "thinking_level": "minimal"},
        ]
        for payload in invalid_payloads:
            with app_module.app.test_request_context(json=payload):
                _, status = app_module._validate_generate_params(payload)
            self.assertEqual(400, status)

    def test_chat_config_applies_thinking_only_to_supported_models(self):
        calls = []

        class FakeChats:
            def create(self, **kwargs):
                calls.append(kwargs)
                return object()

        fake_client = SimpleNamespace(chats=FakeChats())
        session_ids = [str(uuid.uuid4()) for _ in range(6)]
        try:
            with patch.object(app_module, "client", fake_client):
                app_module.create_chat(
                    session_ids[0], model="gemini-3.1-flash-image", thinking_level="minimal"
                )
                app_module.create_chat(
                    session_ids[1], model="gemini-3.1-flash-image", thinking_level="high"
                )
                app_module.create_chat(
                    session_ids[2], model="gemini-3.1-flash-lite-image", thinking_level="minimal"
                )
                app_module.create_chat(
                    session_ids[3], model="gemini-3.1-flash-lite-image", thinking_level="high"
                )
                app_module.create_chat(session_ids[4], model="gemini-3-pro-image")
                app_module.create_chat(session_ids[5], model="gemini-2.5-flash-image")
        finally:
            with app_module.active_chats_lock:
                for session_id in session_ids:
                    app_module.active_chats.pop(session_id, None)

        self.assertEqual(app_module.types.ThinkingLevel.MINIMAL, calls[0]["config"].thinking_config.thinking_level)
        self.assertEqual(app_module.types.ThinkingLevel.HIGH, calls[1]["config"].thinking_config.thinking_level)
        self.assertEqual(app_module.types.ThinkingLevel.MINIMAL, calls[2]["config"].thinking_config.thinking_level)
        self.assertEqual(app_module.types.ThinkingLevel.HIGH, calls[3]["config"].thinking_config.thinking_level)
        self.assertIsNone(calls[4]["config"].thinking_config)
        self.assertIsNone(calls[5]["config"].thinking_config)

    def test_chat_cache_key_includes_thinking_level(self):
        calls = []

        class FakeChats:
            def create(self, **kwargs):
                chat = object()
                calls.append(chat)
                return chat

        session_id = str(uuid.uuid4())
        try:
            with patch.object(app_module, "client", SimpleNamespace(chats=FakeChats())):
                first = app_module.get_or_create_chat(
                    session_id, model="gemini-3.1-flash-image", thinking_level="minimal"
                )
                reused = app_module.get_or_create_chat(
                    session_id, model="gemini-3.1-flash-image", thinking_level="minimal"
                )
                rebuilt = app_module.get_or_create_chat(
                    session_id, model="gemini-3.1-flash-image", thinking_level="high"
                )
        finally:
            with app_module.active_chats_lock:
                app_module.active_chats.pop(session_id, None)

        self.assertIs(first, reused)
        self.assertIsNot(first, rebuilt)
        self.assertEqual(2, len(calls))

    def test_legacy_settings_receive_model_appropriate_thinking_default(self):
        flash_settings = app_module._normalize_session_settings({"model": "gemini-3.1-flash-image"})
        pro_settings = app_module._normalize_session_settings({"model": "gemini-3-pro-image"})
        self.assertEqual("minimal", flash_settings["thinking_level"])
        self.assertIsNone(pro_settings["thinking_level"])

    def test_json_helper_rejects_non_object_payloads(self):
        with app_module.app.test_request_context(json=["not", "an", "object"]):
            self.assertEqual({}, app_module._get_json_data())


if __name__ == "__main__":
    unittest.main()
