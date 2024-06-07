from datetime import datetime, timedelta


class MicroserviceToken:
    def __init__(self):
        self.token = None
        self.expiry = None

    def is_valid(self):
        return self.token and self.expiry and self.expiry > datetime.utcnow()

    def refresh(self, token, expires_in):
        self.token = token
        self.expiry = datetime.utcnow() + timedelta(seconds=expires_in)
