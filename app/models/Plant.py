from mongoengine import Document, fields


class Plant(Document):
    scientific_name = fields.StringField(max_length=100, unique=True, required=True)
    common_names = fields.DictField()
    description = fields.DictField()
    medicinal_uses = fields.DictField()
    chemical_compounds = fields.ListField(fields.StringField())
    image_urls = fields.ListField(fields.StringField())
    conservation_status = fields.StringField(max_length=20)

    meta = {"collection": "plants", "indexes": ["scientific_name"]}

    def to_dict(self):
        return {
            "id": str(self.id),
            "scientific_name": self.scientific_name,
            "common_names": self.common_names,
            "description": self.description,
            "medicinal_uses": self.medicinal_uses,
            "chemical_compounds": self.chemical_compounds,
            "image_urls": self.image_urls,
            "conservation_status": self.conservation_status,
        }
