from app.models import Plant
from mongoengine import Document, fields


class ResearchPublication(Document):
    title = fields.StringField(max_length=200, required=True)
    authors = fields.ListField(fields.StringField())
    abstract = fields.StringField()
    doi = fields.StringField(max_length=100, unique=True)
    publication_date = fields.DateField()
    plants = fields.ListField(fields.ReferenceField(Plant))
    full_text = fields.StringField()
    chemical_compounds = fields.DictField()
    molecular_targets = fields.DictField()

    meta = {"collection": "research_publications", "indexes": ["doi", "-publication_date"]}

    def to_dict(self):
        return {
            "id": str(self.id),
            "title": self.title,
            "authors": self.authors,
            "abstract": self.abstract,
            "doi": self.doi,
            "publication_date": self.publication_date.isoformat() if self.publication_date else None,
            "plants": [str(plant.id) for plant in self.plants],
            "full_text": self.full_text,
            "chemical_compounds": self.chemical_compounds,
            "molecular_targets": self.molecular_targets,
        }
