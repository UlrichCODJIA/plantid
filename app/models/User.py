from datetime import datetime
from typing import Optional


class User:
    """
    Represents a user in the system.

    Attributes:
        id (str): The ID of the user.
        username (str): The username of the user.
        email (str): The email address of the user.
        first_name (Optional[str]): The first name of the user.
        last_name (Optional[str]): The last name of the user.
        language_preference (str): The language preference of the user.
        voice_preference (Optional[str]): The voice preference of the user.
        image_generation_style (Optional[str]): The preferred image generation style of the user.
        registration_date (datetime): The registration date of the user.
        role (str): The role of the user.
    """

    def __init__(self, data):
        self.id: str = data.get("_id")
        self.username: str = data.get("username")
        self.email: str = data.get("email")
        self.first_name: Optional[str] = data.get("firstName")
        self.last_name: Optional[str] = data.get("lastName")
        self.language_preference: str = data.get("languagePreference", "English")
        self.voice_preference: Optional[str] = data.get("voicePreference")
        self.image_generation_style: Optional[str] = data.get("imageGenerationStyle")
        self.registration_date: datetime = datetime.fromisoformat(
            data.get("registrationDate")
        )
        self.role: str = data.get("role", "user")
