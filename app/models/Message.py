from datetime import datetime

from mongoengine import Document, fields


class Message(Document):
    conversation_id = fields.ReferenceField("Conversation", required=True)
    text = fields.StringField()
    translated_text = fields.StringField()
    timestamp = fields.DateTimeField(default=datetime.utcnow)
    sender = fields.StringField(required=True, choices=["user", "bot"])
    audio_data = fields.URLField()

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
            "translated_text": self.translated_text,
            "timestamp": self.timestamp.isoformat(),
            "sender": self.sender,
            "audio_data": self.audio_data,
        }
