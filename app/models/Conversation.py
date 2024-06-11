from datetime import datetime
from mongoengine import (
    Document,
    StringField,
    DateTimeField,
    ReferenceField,
    ListField,
    DictField,
)


class Conversation(Document):
    user_id = StringField(required=True)
    timestamp = DateTimeField(default=datetime.utcnow)
    title = StringField(required=True)
    input_language = StringField()
    output_language = StringField()
    dialogue_state = StringField(default="greeting")
    messages = ListField(ReferenceField("Message"))

    # Fields for tracking image generation task
    image_task_id = StringField()
    image_task_status = StringField(
        default="SUCCESS", choices=["STARTED", "SUCCESS", "FAILURE", "PENDING"]
    )
    image_task_started_at = DateTimeField()
    image_task_completed_at = DateTimeField()

    meta = {
        "indexes": [
            {
                "fields": ["user_id", "timestamp"],
                "unique": False,
            }
        ]
    }

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat(),
            "title": self.title,
            "input_language": self.input_language,
            "output_language": self.output_language,
            "dialogue_state": self.dialogue_state,
            "messages": [message.to_dict() for message in self.messages],
            "image_task_id": self.image_task_id,
            "image_task_status": self.image_task_status,
            "image_task_started_at": (
                self.image_task_started_at.isoformat()
                if self.image_task_started_at
                else None
            ),
            "image_task_completed_at": (
                self.image_task_completed_at.isoformat()
                if self.image_task_completed_at
                else None
            ),
        }
