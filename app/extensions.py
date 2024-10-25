import logging
import os

import boto3
from app.managers.anthropic_api_manager import AnthropicAPIManager
from app.managers.celery_manager import CeleryManager
from app.managers.knowledge_graph_manager import KnowledgeGraphManager
from app.managers.redis_manager import RedisManager
from dotenv import load_dotenv

# from elasticsearch import Elasticsearch
from flasgger import Swagger
from flask_jwt_extended import JWTManager
from flask_session import Session
from logger import configure_logger

load_dotenv()

logger = configure_logger(log_level=logging.DEBUG, log_file="logs/app.log")

chat_logger = configure_logger(log_level=logging.DEBUG, log_file="logs/chat.log")

celery_logger = configure_logger(log_level=logging.DEBUG, log_file="logs/celery.log")

s3 = boto3.client("s3", region_name=os.environ.get("AWS_REGION"))
events = boto3.client("events", region_name=os.environ.get("AWS_REGION"))
lambda_client = boto3.client("lambda", region_name=os.environ.get("AWS_REGION"))
jwt = JWTManager()
session = Session()
celery_manager = CeleryManager()
redis_manager = RedisManager()
anthropic_manager = AnthropicAPIManager()
# elasticsearch = Elasticsearch()
knowledge_graph = KnowledgeGraphManager()

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "PlantId chatbot API",
        "description": "API documentation for the PlantId chatbot service",
        "version": "1.0.0",
    },
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT token for authentication. Example: 'Bearer {token}'",
        }
    },
    "security": [{"Bearer": []}],
}
swagger = Swagger(template=swagger_template)
