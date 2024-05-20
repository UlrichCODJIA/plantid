import logging
import time
from flask_jwt_extended import JWTManager
import redis
from flask import Flask, jsonify
from flask_session import Session
from datetime import timedelta
import whisper
from transformers import pipeline
from mmtafrica.mmtafrica import load_params

import torch
from logger import configure_logger
from sentence_transformers import SentenceTransformer
import tensorflow_hub as hub
from transformers import LlavaNextProcessor, LlavaNextForConditionalGeneration

logger = configure_logger(log_level=logging.DEBUG, log_file="app.log")


def create_app(args):
    app = Flask(__name__)
    if args.environment == "production":
        app.config.from_object("config.settings.ProdConfig")
    else:
        app.config.from_object("config.settings.DevConfig")
    app.secret_key = app.config["SECRET_KEY"]

    # Database configuration
    from models.models import db

    app.db = db
    app.db.init_app(app)

    # Redis connection parameters
    redis_url = app.config["REDIS_URL"]
    redis_retries = 3  # Number of retries
    redis_retry_delay = 5  # Delay between retries in seconds

    # Configure Redis for session storage with error handling and retries
    app.redis_client = None
    for _ in range(redis_retries):
        try:
            app.redis_client = redis.from_url(redis_url)
            app.redis_client.ping()  # Test the connection
            logger.info("Connected to Redis successfully!")
            break  # Exit the loop if connection successful
        except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as e:
            logger.error(f"Error connecting to Redis: {e}")
            logger.info(f"Retrying in {redis_retry_delay} seconds...")
            time.sleep(redis_retry_delay)

    if app.redis_client is None:
        logger.warning(
            "Falling back to filesystem sessions due to Redis connection issues."
        )
        app.config["SESSION_TYPE"] = "filesystem"
    else:
        app.config["SESSION_TYPE"] = "redis"
        app.config["SESSION_REDIS"] = app.redis_client
        app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)

    # Configure JWT
    app.jwt = JWTManager(app)
    Session(app)

    device = "cpu"
    if torch.cuda.is_available():
        device = "gpu"

    # Load the sentence embedding model and attach to the app object
    app.sentence_embedding_model = SentenceTransformer("all-mpnet-base-v2")
    logger.info("Sentence embedding model loaded successfully!")

    # Load the TensorFlow image recognition model
    app.image_recognition_model = hub.load(
        "https://tfhub.dev/google/imagenet/mobilenet_v2_100_224/classification/5"
    )
    logger.info("TensorFlow image recognition model loaded successfully!")

    # --- Initialize the LLaVA model ---
    app.llava_processor = LlavaNextProcessor.from_pretrained(
        "llava-hf/llava-v1.6-mistral-7b-hf"
    )
    app.llava_model = LlavaNextForConditionalGeneration.from_pretrained(
        "llava-hf/llava-v1.6-mistral-7b-hf",
        torch_dtype=torch.float16,
        low_cpu_mem_usage=True,
    )
    if device == "gpu":
        app.llava_model.to("cuda")
    logger.info("LLaVA model loaded successfully!")

    # --- Initialize the Whisper's models ---
    app.whisper_base_model = whisper.load_model("base")
    app.whisper_yoruba_pipeline = pipeline(
        "automatic-speech-recognition", model="neoform-ai/whisper-medium-yoruba"
    )
    app.whisper_fon_pipeline = pipeline(
        "automatic-speech-recognition", model="chrisjay/fonxlsr"
    )
    logger.info("Whisper's models loaded successfully!")

    # --- Initialize the MMTAFRICA model ---
    checkpoint = "ai_models/mmt_translation.pt"
    app.mmt_params = load_params({"checkpoint": checkpoint, "device": device})
    logger.info("MMTAFRICA model loaded successfully!")

    # Initialize and register blueprints, extensions, etc.
    from app.chatbot import chatbot_blueprint

    app.register_blueprint(chatbot_blueprint, url_prefix="/chatbot")

    from app.auth import auth_blueprint

    app.register_blueprint(auth_blueprint, url_prefix="/auth")

    @app.errorhandler(redis.exceptions.RedisError)
    def handle_redis_error(e):
        logger.error(f"Redis Error: {e}")
        return (
            jsonify({"error": "A database error occurred. Please try again later."}),
            500,
        )

    return app
