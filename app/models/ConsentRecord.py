from datetime import datetime

from mongoengine import Document, fields


class ConsentRecord(Document):
    user_id = fields.StringField(required=True)
    consent_type = fields.StringField(max_length=50, required=True)
    provider_name = fields.StringField(max_length=100, required=True)
    community = fields.StringField(max_length=100)
    consent_date = fields.DateTimeField(default=datetime.utcnow)
    expiry_date = fields.DateTimeField()
    terms = fields.DictField()
    verification_method = fields.StringField(max_length=50)
    verification_details = fields.DictField()

    meta = {"collection": "consent_records", "indexes": [("user_id", "consent_type")]}

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "consent_type": self.consent_type,
            "provider_name": self.provider_name,
            "community": self.community,
            "consent_date": self.consent_date.isoformat(),
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "terms": self.terms,
            "verification_method": self.verification_method,
            "verification_details": self.verification_details,
        }
