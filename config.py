from datetime import timedelta
import logging
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base Configuration"""

    DEBUG = False  # Set to True for development mode
    TESTING = False  # Set to True when running tests

    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)

    WTF_CSRF_ENABLED = True

    # Secret Key (for sessions and other security features)
    SECRET_KEY = os.environ.get("SECRET_KEY")

    # Database Configuration (PostgreSQL example)
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Redis Configuration
    SESSION_TYPE = "redis"
    REDIS_URL = os.environ.get("REDIS_URL")

    CELERY_BROKER_URL = os.environ.get("REDIS_URL")
    CELERY_RESULT_BACKEND = os.environ.get("REDIS_URL")

    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get("PLANTID_DB_API_JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    CHATBOT_JWT_SECRET_KEY = os.environ.get("CHATBOT_JWT_SECRET_KEY")
    CHATBOT_JWT_ACCESS_EXPIRES_IN = os.environ.get("CHATBOT_JWT_ACCESS_EXPIRES_IN")

    # Redis for Token Blocklist
    JWT_BLOCKLIST_ENABLED = True
    JWT_BLOCKLIST_TOKEN_CHECKS = ["access", "refresh"]

    # Logging Configuration
    LOG_LEVEL = logging.INFO  # (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    # Other Settings (customize as needed)
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
    ALLOWED_EXTENSIONS = {"wav", "jpg", "png"}

    # Stability API credentials
    STABILITY_API_KEY = os.environ.get("STABILITY_API_KEY")
    STABILITY_API_HOST = os.environ.get("STABILITY_API_HOST")

    # Replicate API credentials
    REPLICATE_API_KEY = os.environ.get("REPLICATE_API_KEY")

    # Eleven Labs API credentials
    ELEVEN_LABS_VOICE_ID = os.environ.get("ELEVEN_LABS_VOICE_ID")
    ELEVEN_LABS_API_KEY = os.environ.get("ELEVEN_LABS_API_KEY")


class ProdConfig(Config):
    FLASK_ENV = "production"
    WTF_CSRF_ENABLED = False


class DevConfig(Config):
    FLASK_ENV = "development"
    DEBUG = True

    WTF_CSRF_ENABLED = False

    # Use an in-memory SQLite database for testing
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Faster token expiration for testing
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=5)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(seconds=10)


class TestConfig(Config):
    TESTING = True

    WTF_CSRF_ENABLED = False

    # Use an in-memory SQLite database for testing
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Faster token expiration for testing
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=5)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(seconds=10)
