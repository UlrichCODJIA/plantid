import logging
import os
from datetime import timedelta


class Config:
    """Base Configuration"""

    DEBUG = False  # Set to True for development mode
    TESTING = False  # Set to True when running tests

    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)

    WTF_CSRF_ENABLED = True

    # Secret Key (for sessions and other security features)
    SECRET_KEY = os.environ.get("SECRET_KEY")

    # Database Configuration
    MONGODB_DB = os.environ.get("MONGODB_DB")
    MONGODB_HOST = os.environ.get("MONGODB_HOST")
    MONGODB_PORT = os.environ.get("MONGODB_PORT")
    MONGODB_USERNAME = os.environ.get("MONGODB_USERNAME")
    MONGODB_PASSWORD = os.environ.get("MONGODB_PASSWORD")

    # Redis Configuration
    SESSION_TYPE = "redis"
    REDIS_URL = os.environ.get("REDIS_URL") or "redis://localhost:6379"

    # Rate Limiting Configuration
    RATELIMIT_STORAGE_OPTIONS = {"socket_connect_timeout": 30}
    RATELIMIT_STRATEGY = "moving-window"

    # Celery Configuration
    CELERY = dict(
        broker_url=os.environ.get("CELERY_REDIS_URL"),
        result_backend=os.environ.get("CELERY_REDIS_URL"),
        task_ignore_result=True,
        broker_connection_retry_on_startup=True,
        include=["app.tasks.tasks"],
    )

    SWAGGER = {
        "title": "PlantId chatbot API",
        "uiversion": 3,
    }

    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get("PLANTID_DB_API_JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    CHATBOT_JWT_SECRET_KEY = os.environ.get("CHATBOT_JWT_SECRET_KEY")
    CHATBOT_JWT_ACCESS_EXPIRES_IN = os.environ.get("CHATBOT_JWT_ACCESS_EXPIRES_IN")

    PLANTID_DB_API_BASE_URL = os.environ.get("PLANTID_DB_API_BASE_URL")

    # Redis for Token Blocklist
    JWT_BLOCKLIST_ENABLED = True
    JWT_BLOCKLIST_TOKEN_CHECKS = ["access", "refresh"]

    # Logging Configuration
    LOG_LEVEL = logging.INFO  # (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    # Other Settings (customize as needed)
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
    ALLOWED_EXTENSIONS = {"wav", "jpg", "png"}

    # Anthropic API key
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

    # Stability API credentials
    STABILITY_API_KEY = os.environ.get("STABILITY_API_KEY")
    STABILITY_API_HOST = os.environ.get("STABILITY_API_HOST")

    # Replicate API credentials
    REPLICATE_API_KEY = os.environ.get("REPLICATE_API_KEY")

    # Eleven Labs API credentials
    ELEVEN_LABS_VOICE_ID = os.environ.get("ELEVEN_LABS_VOICE_ID")
    ELEVEN_LABS_API_KEY = os.environ.get("ELEVEN_LABS_API_KEY")

    # NEOO4J Configuration
    NEO4J_URL = os.environ.get("NEO4J_URL", "bolt://localhost:7687")
    NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "neo4j")

    BACKUP_STORAGE_PATH = os.environ.get("BACKUP_STORAGE_PATH", "backups")


class ProdConfig(Config):
    FLASK_ENV = "production"
    WTF_CSRF_ENABLED = False


class DevConfig(Config):
    FLASK_ENV = "development"
    DEBUG = True

    WTF_CSRF_ENABLED = False

    # Faster token expiration for testing
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=5)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(seconds=10)


class TestConfig(Config):
    TESTING = True

    WTF_CSRF_ENABLED = False

    # Faster token expiration for testing
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=5)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(seconds=10)
