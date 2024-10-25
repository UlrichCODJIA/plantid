import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "you-will-never-guess"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "postgresql://user:pass@localhost/plantid"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
    REDIS_URL = os.environ.get("REDIS_URL") or "redis://localhost:6379"

    # Cache configuration
    CACHE_TYPE = "redis"
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 300

    # Rate limiting
    RATELIMIT_STORAGE_URL = REDIS_URL

    # Image upload configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max-limit
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

    NEO4J_URL = os.environ.get("NEO4J_URL", "bolt://localhost:7687")
    NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "password")

    BACKUP_STORAGE_PATH = os.environ.get("BACKUP_STORAGE_PATH", "/path/to/backups")

    # Voice processing config
    VOICE_RECOGNITION_MODEL = os.environ.get("VOICE_RECOGNITION_MODEL", "whisper-1")
    TEXT_TO_SPEECH_MODEL = os.environ.get("TEXT_TO_SPEECH_MODEL", "neural-voice-1")
