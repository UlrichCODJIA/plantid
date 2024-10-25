from datetime import datetime

from mongoengine import Document, fields


class AuditLog(Document):
    user_id = fields.StringField(required=True)
    action = fields.StringField(max_length=100)
    details = fields.DictField()
    timestamp = fields.DateTimeField(default=datetime.utcnow)

    meta = {"collection": "audit_logs", "indexes": ["-timestamp"]}

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "action": self.action,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }
