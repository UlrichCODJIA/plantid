from datetime import datetime
from typing import Optional


class User:
    def __init__(self, data):
        self.id: str = data.get("_id")
        self.username: str = data.get("username")
        self.email: str = data.get("email")
        self.first_name: Optional[str] = data.get("firstName")
        self.last_name: Optional[str] = data.get("lastName")
        self.language_preference: str = data.get("languagePreference", "English")
        self.voice_preference: Optional[str] = data.get("voicePreference")
        self.expertise_level: Optional[str] = data.get("expertiseLevel", "beginner")
        self.is_verified_researcher: bool = data.get("isVerifiedResearcher", False)
        self.role: str = data.get("role", "user")

    def parse_date(self, date_string):
        if date_string:
            return datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S.%fZ")
        return None

    def __str__(self):
        return f"User(id={self.id}, username={self.username}, email={self.email})"

    def __repr__(self):
        return self.__str__()
