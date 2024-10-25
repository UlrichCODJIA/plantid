import logging
import os

from logger import configure_logger
from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError

logger = configure_logger(log_level=logging.DEBUG, log_file="logs/knowledge_graph.log")


class KnowledgeGraphManager:
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.config.setdefault("NEO4J_URL", os.environ.get("NEO4J_URL"))
        app.config.setdefault("NEO4J_USER", os.environ.get("NEO4J_USER"))
        app.config.setdefault("NEO4J_PASSWORD", os.environ.get("NEO4J_PASSWORD"))

        self.driver = GraphDatabase.driver(
            app.config["NEO4J_URL"], auth=(app.config["NEO4J_USER"], app.config["NEO4J_PASSWORD"])
        )

    def add_plant(self, plant):
        try:
            with self.driver.session() as session:
                session.execute_write(self._create_plant, plant)
        except Neo4jError as e:
            logger.error(f"Neo4j error: {str(e)}")
            raise

    @staticmethod
    def _create_plant(tx, plant):
        query = """
        CREATE (p:Plant {
            id: $id,
            scientific_name: $scientific_name,
            common_names: $common_names
        })
        WITH p
        UNWIND $compounds as compound
        MERGE (c:Compound {name: compound})
        CREATE (p)-[:CONTAINS]->(c)
        """
        tx.run(
            query,
            id=plant.id,
            scientific_name=plant.scientific_name,
            common_names=list(plant.common_names.values())[0],
            compounds=plant.chemical_compounds,
        )

    def add_traditional_knowledge(self, knowledge):
        with self.driver.session() as session:
            session.execute_write(self._create_traditional_knowledge, knowledge)

    @staticmethod
    def _create_traditional_knowledge(tx, knowledge):
        query = """
        MATCH (p:Plant {id: $plant_id})
        CREATE (tk:TraditionalKnowledge {
            id: $id,
            region: $region
        })
        CREATE (p)-[:HAS_KNOWLEDGE]->(tk)
        """
        tx.run(query, plant_id=knowledge.plant_id, id=knowledge.id, region=knowledge.source_region)

    def add_publication(self, publication):
        with self.driver.session() as session:
            session.execute_write(self._create_publication, publication)

    @staticmethod
    def _create_publication(tx, publication):
        query = """
        CREATE (pub:Publication {
            id: $id,
            title: $title,
            doi: $doi
        })
        WITH pub
        UNWIND $plant_ids as plant_id
        MATCH (p:Plant {id: plant_id})
        CREATE (pub)-[:STUDIES]->(p)
        """
        plant_ids = [plant.id for plant in publication.plants]
        tx.run(query, id=publication.id, title=publication.title, doi=publication.doi, plant_ids=plant_ids)
