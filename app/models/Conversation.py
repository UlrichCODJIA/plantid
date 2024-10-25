from datetime import datetime

from mongoengine import Document, fields


class Conversation(Document):
    user_id = fields.StringField(required=True)
    timestamp = fields.DateTimeField(default=datetime.utcnow)
    title = fields.StringField(required=True)
    input_language = fields.StringField()
    output_language = fields.StringField()
    dialogue_state = fields.StringField(default="greeting")
    messages = fields.ListField(fields.ReferenceField("Message"))

    safety_warnings_given = fields.ListField(fields.StringField())
    consultation_reminder_given = fields.BooleanField(default=False)

    meta = {
        "indexes": [
            {
                "fields": ["user_id", "timestamp"],
                "unique": False,
            },
        ]
    }

    def add_safety_warning(self, warning):
        if warning not in self.safety_warnings_given:
            self.safety_warnings_given.append(warning)
            self.save()

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
            "safety_warnings_given": self.safety_warnings_given,
            "consultation_reminder_given": self.consultation_reminder_given,
        }
