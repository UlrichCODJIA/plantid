from datetime import datetime

from mongoengine import Document, fields


class FieldResearchData(Document):
    researcher_id = fields.StringField(required=True)
    plant_id = fields.StringField(required=True)
    location = fields.DictField()
    collection_date = fields.DateTimeField(default=datetime.utcnow)
    environmental_conditions = fields.DictField()
    samples_collected = fields.DictField()
    observations = fields.StringField()
    images = fields.DictField()
    verified = fields.BooleanField(default=False)

    meta = {"collection": "field_research_data", "indexes": [("researcher_id", "plant_id"), "collection_date"]}

    def to_dict(self):
        return {
            "id": str(self.id),
            "researcher_id": self.researcher_id,
            "plant_id": self.plant_id,
            "location": self.location,
            "collection_date": self.collection_date.isoformat(),
            "environmental_conditions": self.environmental_conditions,
            "samples_collected": self.samples_collected,
            "observations": self.observations,
            "images": self.images,
            "verified": self.verified,
        }
