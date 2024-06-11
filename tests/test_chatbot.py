from argparse import ArgumentParser
import os
import sys
import unittest
import json
import tempfile
import pyttsx3
from PIL import Image
import requests_mock

from app import create_app
from app.extensions import db
from app.models.Conversation import Conversation


class ChatbotTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.args = cls._parse_command_line_args()

    @classmethod
    def _parse_command_line_args(cls):
        parser = ArgumentParser(
            description="PLANTID - A plant identification application"
        )
        parser.add_argument(
            "--environment",
            type=str,
            default="development",
            choices=["development", "production"],
            help="Specify the app environment. Default is development.",
        )
        parser.add_argument(
            "--username", type=str, required=True, help="Specify the username."
        )
        parser.add_argument(
            "--password", type=str, required=True, help="Specify the user password"
        )
        return parser.parse_args()

    def setUp(self):
        self._create_app_context()
        self.client = self.app.test_client()
        self.access_token = self._get_access_token()

    def tearDown(self):
        self._remove_app_context()

    def _create_app_context(self):
        self.app = create_app(self.args)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def _remove_app_context(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def _get_access_token(self):
        response = self.client.post(
            f"{os.environ.get('PLANTID_DB_API_BASE_URL')}/api/auth/login",
            json={"username": self.args.username, "password": self.args.password},
        )
        data = json.loads(response.data)
        return data["access_token"]

    def _create_temp_audio(self):
        temp_audio = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_audio_path = temp_audio.name
        temp_audio.close()
        engine = pyttsx3.init()
        engine.save_to_file("This is a test audio.", temp_audio_path)
        engine.runAndWait()
        return temp_audio_path

    def _create_temp_image(self):
        temp_image = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        temp_image_path = temp_image.name
        image = Image.new("RGB", (100, 100), color="blue")
        image.save(temp_image_path)
        return temp_image_path

    def test_chat_text_input(self):
        response = self.client.post(
            "/chat",
            headers={"Authorization": f"Bearer {self.access_token}"},
            data={"text": "Hello, how are you?", "language": "English"},
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("response", data)
        self.assertTrue(len(data["response"]) > 0)

    def test_chat_voice_input(self):
        temp_audio_path = self._create_temp_audio()
        with open(temp_audio_path, "rb") as audio:
            response = self.client.post(
                "/chat",
                headers={"Authorization": f"Bearer {self.access_token}"},
                data={"language": "English", "audio": (audio, "test_audio.wav")},
            )
        os.remove(temp_audio_path)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("response", data)
        self.assertTrue(len(data["response"]) > 0)

    def test_chat_image_input(self):
        temp_image_path = self._create_temp_image()
        with open(temp_image_path, "rb") as img:
            response = self.client.post(
                "/chat",
                headers={"Authorization": f"Bearer {self.access_token}"},
                data={"language": "English", "image": (img, "test_image.jpg")},
            )
        os.remove(temp_image_path)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("response", data)
        self.assertIn("blue", data["response"].lower())

    def test_chat_invalid_input(self):
        temp_audio_path = self._create_temp_audio()
        with open(temp_audio_path, "rb") as audio:
            response = self.client.post(
                "/chat",
                headers={"Authorization": f"Bearer {self.access_token}"},
                data={
                    "language": "English",
                    "audio": (audio, "test_audio.wav"),
                    "text": "Hello",
                },
            )
        os.remove(temp_audio_path)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn("error", data)

    def test_image_generation(self):
        test_prompt = "Generate an image of a sunset"
        with requests_mock.Mocker() as m:
            mock_response_data = {
                "image_url": "https://example.com/generated_image.jpg"
            }
            m.post(
                "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
                json=mock_response_data,
            )
            response = self.client.post(
                "/chat",
                headers={"Authorization": f"Bearer {self.access_token}"},
                data={
                    "text": test_prompt,
                    "language": "English",
                    "generate_image": True,
                },
            )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("response", data)
        self.assertIn("image_task_id", data)

        task_id = data["image_task_id"]
        status_response = self.client.get(
            f"/chat/image-status/{task_id}",
            headers={"Authorization": f"Bearer {self.access_token}"},
        )
        self.assertEqual(status_response.status_code, 200)
        status_data = json.loads(status_response.data)
        self.assertEqual(status_data["status"], "SUCCESS")
        self.assertEqual(status_data["image_url"], mock_response_data["image_url"])

    def test_image_generation_error(self):
        test_prompt = "Generate an image of a sunset"
        with requests_mock.Mocker() as m:
            m.post(
                "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
                status_code=500,
            )
            response = self.client.post(
                "/chat",
                headers={"Authorization": f"Bearer {self.access_token}"},
                data={
                    "text": test_prompt,
                    "language": "English",
                    "generate_image": True,
                },
            )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("image_task_id", data)

        task_id = data["image_task_id"]
        status_response = self.client.get(
            f"/chat/image-status/{task_id}",
            headers={"Authorization": f"Bearer {self.access_token}"},
        )
        self.assertEqual(status_response.status_code, 200)
        status_data = json.loads(status_response.data)
        self.assertEqual(status_data["status"], "FAILURE")

    def test_unauthorized_access(self):
        response = self.client.post("/chat", data={"text": "Hello"})
        self.assertEqual(response.status_code, 401)

    def test_chat_language_preference(self):
        self.test_user.language_preference = "French"
        db.session.commit()
        response = self.client.post(
            "/chat",
            headers={"Authorization": f"Bearer {self.access_token}"},
            data={"text": "Bonjour, comment allez-vous?", "language": "French"},
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("response", data)
        self.assertIn("bonjour", data["response"].lower())

    def test_dialogue_management_greeting(self):
        response = self.client.post(
            "/chat",
            headers={"Authorization": f"Bearer {self.access_token}"},
            data={"text": "Hi", "language": "English"},
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("response", data)
        self.assertIn("How can I help you today?", data["response"])

        conversation = Conversation.query.filter_by(user_id=self.test_user.id).first()
        self.assertEqual(conversation.dialogue_state, "conversing")

    def test_dialogue_management_conversing(self):
        self.client.post(
            "/chat",
            headers={"Authorization": f"Bearer {self.access_token}"},
            data={"text": "Hi", "language": "English"},
        )
        response = self.client.post(
            "/chat",
            headers={"Authorization": f"Bearer {self.access_token}"},
            data={"text": "Tell me a joke", "language": "English"},
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("response", data)
        self.assertIn("joke", data["response"].lower())

        conversation = Conversation.query.filter_by(user_id=self.test_user.id).first()
        self.assertEqual(conversation.dialogue_state, "conversing")


if __name__ == "__main__":
    unittest.main()
