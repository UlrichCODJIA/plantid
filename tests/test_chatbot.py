from argparse import ArgumentParser
import os
import sys
import unittest
import json
import tempfile
import pyttsx3
from PIL import Image
from app import create_app, db
from models.models import User, Conversation
import requests_mock


class ChatbotTestCase(unittest.TestCase):
    def setUp(self):
        # Simulate command line arguments
        sys.argv = ["test_chatbot.py", "--environment", "production"]

        # Parse arguments
        parser = ArgumentParser(
            description="PLANTID - A plant identification application"
        )
        parser.add_argument(
            "--environment",
            type=str,
            default="development",
            choices=["development", "production"],
            help="Specify the app environment. Possible values:"
            " development, production. Default is development.",
        )
        args = parser.parse_args()

        self.app = create_app(args)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create a test user
        self.test_user = User(username="testuser", email="testuser@example.com")
        self.test_user.set_password("testpassword")
        db.session.add(self.test_user)
        db.session.commit()

        self.client = self.app.test_client()
        self.access_token = self.get_access_token()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def get_access_token(self):
        response = self.client.post(
            "/auth/login",
            json={"username": "testuser", "password": "testpassword"},
        )
        data = json.loads(response.data)
        return data["access_token"]

    # --- Helper Functions for Creating Test Data ---

    def create_test_audio(self):
        """Creates a temporary audio file with some test content."""
        temp_audio = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_audio_path = temp_audio.name
        temp_audio.close()  # Close the file, so pyttsx3 can write to it

        # Use pyttsx3 to generate some speech
        engine = pyttsx3.init()
        engine.save_to_file("This is a test audio.", temp_audio_path)
        engine.runAndWait()

        return temp_audio_path

    def create_test_image(self):
        """Creates a temporary image file."""
        temp_image = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        temp_image_path = temp_image.name
        image = Image.new("RGB", (100, 100), color="blue")
        image.save(temp_image_path)
        return temp_image_path

    # --- Test Cases ---

    def test_chat_text_input(self):
        response = self.client.post(
            "/chatbot/chat",
            headers={"Authorization": f"Bearer {self.access_token}"},
            data={"text": "Hello, how are you?", "language": "English"},
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("response", data)
        self.assertTrue(len(data["response"]) > 0)

    def test_chat_voice_input(self):
        temp_audio_path = self.create_test_audio()
        with open(temp_audio_path, "rb") as audio:
            response = self.client.post(
                "/chatbot/chat",
                headers={"Authorization": f"Bearer {self.access_token}"},
                data={"language": "English", "audio": (audio, "test_audio.wav")},
            )
        os.remove(temp_audio_path)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("response", data)
        self.assertTrue(len(data["response"]) > 0)

    def test_chat_image_input(self):
        temp_image_path = self.create_test_image()
        with open(temp_image_path, "rb") as img:
            response = self.client.post(
                "/chatbot/chat",
                headers={"Authorization": f"Bearer {self.access_token}"},
                data={"language": "English", "image": (img, "test_image.jpg")},
            )
        os.remove(temp_image_path)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("response", data)
        self.assertIn(
            "blue", data["response"].lower()
        )  # Check if the response mentions "blue"

    def test_chat_image_url_input(self):
        test_image_url = "https://example.com/test_image.jpg"
        with requests_mock.Mocker() as m:
            # Mock the image download
            m.get(test_image_url, content=b"mock image content")
            response = self.client.post(
                "/chatbot/chat",
                headers={"Authorization": f"Bearer {self.access_token}"},
                data={"language": "English", "image_url": test_image_url},
            )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("response", data)
        self.assertTrue(len(data["response"]) > 0)

    def test_chat_invalid_input(self):
        # Test sending both text and audio
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            temp_audio_path = temp_audio.name
            # Use pyttsx3 to generate some speech
            engine = pyttsx3.init()
            engine.save_to_file("This is a test audio.", temp_audio_path)
            engine.runAndWait()

        with open(temp_audio_path, "rb") as audio:
            response = self.client.post(
                "/chatbot/chat",
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
            # Mock the image generation API response
            mock_response_data = {
                "image_url": "https://example.com/generated_image.jpg"
            }
            m.post(
                "https://api.stability.ai/v1/generation/"
                "stable-diffusion-xl-1024-v1-0/text-to-image",
                json=mock_response_data,
            )
            response = self.client.post(
                "/chatbot/chat",
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

        # Check image generation status
        task_id = data["image_task_id"]
        status_response = self.client.get(
            f"/chatbot/image-status/{task_id}",
            headers={"Authorization": f"Bearer {self.access_token}"},
        )
        self.assertEqual(status_response.status_code, 200)
        status_data = json.loads(status_response.data)
        self.assertEqual(status_data["status"], "SUCCESS")
        self.assertEqual(status_data["image_url"], mock_response_data["image_url"])

    def test_image_generation_error(self):
        test_prompt = "Generate an image of a sunset"
        with requests_mock.Mocker() as m:
            # Mock an error from the image generation API
            m.post(
                "https://api.stability.ai/v1/generation/"
                "stable-diffusion-xl-1024-v1-0/text-to-image",
                status_code=500,
            )
            response = self.client.post(
                "/chatbot/chat",
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
            f"/chatbot/image-status/{task_id}",
            headers={"Authorization": f"Bearer {self.access_token}"},
        )
        self.assertEqual(status_response.status_code, 200)
        status_data = json.loads(status_response.data)
        self.assertEqual(status_data["status"], "FAILURE")

    def test_unauthorized_access(self):
        response = self.client.post("/chatbot/chat", data={"text": "Hello"})
        self.assertEqual(response.status_code, 401)  # Unauthorized

    def test_chat_language_preference(self):
        """Tests that the chatbot uses the user's language preference."""
        self.test_user.language_preference = "French"
        db.session.commit()
        response = self.client.post(
            "/chatbot/chat",
            headers={"Authorization": f"Bearer {self.access_token}"},
            data={"text": "Bonjour, comment allez-vous?", "language": "French"},
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("response", data)
        self.assertIn(
            "bonjour", data["response"].lower()
        )  # Check for a French greeting

    def test_dialogue_management_greeting(self):
        """Tests the initial greeting state."""
        response = self.client.post(
            "/chatbot/chat",
            headers={"Authorization": f"Bearer {self.access_token}"},
            data={"text": "Hi", "language": "English"},
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("response", data)
        self.assertIn("How can I help you today?", data["response"])

        # Check that the dialogue state is updated in the database
        conversation = Conversation.query.filter_by(user_id=self.test_user.id).first()
        self.assertEqual(conversation.dialogue_state, "conversing")

    def test_dialogue_management_conversing(self):
        """Tests the conversing state."""
        # Send an initial message to transition to the "conversing" state
        self.client.post(
            "/chatbot/chat",
            headers={"Authorization": f"Bearer {self.access_token}"},
            data={"text": "Hi", "language": "English"},
        )

        # Send a message in the "conversing" state
        response = self.client.post(
            "/chatbot/chat",
            headers={"Authorization": f"Bearer {self.access_token}"},
            data={"text": "Tell me a joke", "language": "English"},
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("response", data)
        self.assertTrue(len(data["response"]) > 0)

    def test_dialogue_management_confirming(self):
        """Tests transitioning to and from the confirming state."""
        # Send messages to get to the "confirming" state
        self.client.post(
            "/chatbot/chat",
            headers={"Authorization": f"Bearer {self.access_token}"},
            data={"text": "Hi", "language": "English"},
        )
        self.client.post(
            "/chatbot/chat",
            headers={"Authorization": f"Bearer {self.access_token}"},
            data={"text": "Tell me something", "language": "English"},
        )

        # Test "yes" response
        response = self.client.post(
            "/chatbot/chat",
            headers={"Authorization": f"Bearer {self.access_token}"},
            data={"text": "Yes", "language": "English"},
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("response", data)
        self.assertIn("What else can I do for you?", data["response"])

        # Test "no" response
        response = self.client.post(
            "/chatbot/chat",
            headers={"Authorization": f"Bearer {self.access_token}"},
            data={"text": "No", "language": "English"},
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("response", data)
        self.assertIn("Have a great day!", data["response"])

    def test_dialogue_management_end(self):
        """Tests the end state."""
        # Send messages to get to the "end" state
        self.client.post(
            "/chatbot/chat",
            headers={"Authorization": f"Bearer {self.access_token}"},
            data={"text": "Hi", "language": "English"},
        )
        self.client.post(
            "/chatbot/chat",
            headers={"Authorization": f"Bearer {self.access_token}"},
            data={"text": "Tell me something", "language": "English"},
        )
        self.client.post(
            "/chatbot/chat",
            headers={"Authorization": f"Bearer {self.access_token}"},
            data={"text": "No", "language": "English"},
        )

        response = self.client.post(
            "/chatbot/chat",
            headers={"Authorization": f"Bearer {self.access_token}"},
            data={"text": "Anything else?", "language": "English"},
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("response", data)
        self.assertEqual(data["response"], "Goodbye!")

    def test_redis_error(self):
        """Simulates a Redis connection error."""
        with self.app.app_context():
            self.app.redis_client = None  # Simulate Redis being unavailable

        response = self.client.post(
            "/chatbot/chat",
            headers={"Authorization": f"Bearer {self.access_token}"},
            data={"text": "Hello", "language": "English"},
        )
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertIn("error", data)
        self.assertIn("database error", data["error"].lower())
