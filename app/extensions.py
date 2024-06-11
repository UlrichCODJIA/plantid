from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import JWTManager, get_jwt_identity, verify_jwt_in_request
from flask_session import Session
from flasgger import Swagger
import boto3

from app.managers.celery_manager import CeleryManager
from app.managers.redis_manager import RedisManager

s3 = boto3.client("s3")
events = boto3.client("events")
lambda_client = boto3.client("lambda")
jwt = JWTManager()
session = Session()
celery_manager = CeleryManager()
redis_manager = RedisManager()
limiter = Limiter(
    key_func=lambda: (
        get_jwt_identity()
        if verify_jwt_in_request(optional=True)
        else get_remote_address()
    )
)

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
