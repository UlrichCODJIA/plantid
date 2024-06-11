from datetime import datetime
from mongoengine import Document, StringField, DateTimeField, ReferenceField, URLField


class Message(Document):
    conversation_id = ReferenceField("Conversation", required=True)
    text = StringField()
    timestamp = DateTimeField(default=datetime.utcnow)
    sender = StringField(required=True, choices=["user", "bot"])
    image_url = URLField()
    audio_data = StringField()

    meta = {
        "indexes": [
            {
                "fields": ["conversation_id", "timestamp"],
                "unique": False,
            }
        ]
    }

    def to_dict(self):
        return {
            "id": str(self.id),
            "conversation_id": str(self.conversation_id.id),
            "text": self.text,
            "timestamp": self.timestamp.isoformat(),
            "sender": self.sender,
            "image_url": self.image_url,
            "audio_data": self.audio_data,
        }
