from datetime import datetime, timedelta

from app import chat_logger


class MicroserviceToken:
    def __init__(self):
        self.token = None
        self.expiry = None

    def is_valid(self):
        try:
            return self.token and self.expiry and self.expiry > datetime.utcnow()
        except Exception as e:
            chat_logger.error(f"Error in MicroserviceToken.is_valid: {e}")
            return False

    def refresh(self, token, expires_in):
        self.token = token
        self.expiry = datetime.utcnow() + timedelta(seconds=expires_in)
