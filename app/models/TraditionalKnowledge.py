from datetime import datetime

from mongoengine import Document, fields


class TraditionalKnowledge(Document):
    plant_id = fields.ObjectIdField(required=True)
    contributor_id = fields.StringField(required=True)
    knowledge_text = fields.DictField()
    source_region = fields.StringField(max_length=100)
    verification_status = fields.StringField(max_length=20, default="pending")
    created_at = fields.DateTimeField(default=datetime.utcnow)
    consent_record = fields.DictField()

    meta = {"collection": "traditional_knowledge", "indexes": ["plant_id", "contributor_id", "-created_at"]}

    def to_dict(self):
        return {
            "id": str(self.id),
            "plant_id": str(self.plant_id),
            "contributor_id": self.contributor_id,
            "knowledge_text": self.knowledge_text,
            "source_region": self.source_region,
            "verification_status": self.verification_status,
            "created_at": self.created_at.isoformat(),
            "consent_record": self.consent_record,
        }
