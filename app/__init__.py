import os

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import logging
import redis
from flask import Flask
import whisper

import torch
from logger import configure_logger
from sentence_transformers import SentenceTransformer
import tensorflow_hub as hub
from transformers import (
    # pipeline,
    LlavaNextProcessor,
    LlavaNextForConditionalGeneration,
    # AutoProcessor,
    # AutoModelForSpeechSeq2Seq,
    # AutoModelForCTC,
)

from multilingual_webapp.app.tasks.tasks import celery_app
from multilingual_webapp.app.extensions import db, jwt, session
from multilingual_webapp.utils.utils import retry_on_exception
from multilingual_webapp.app.chatbot.utils.translation.translation import (
    TranslationService,
)

logger = configure_logger(log_level=logging.DEBUG, log_file="logs/app.log")


def create_app(args):
    app = Flask(__name__)
    if args.environment == "production":
        app.config.from_object("multilingual_webapp.config.settings.ProdConfig")
    elif args.environment == "testing":
        app.config.from_object("multilingual_webapp.config.settings.TestConfig")
    else:
        app.config.from_object("multilingual_webapp.config.settings.DevConfig")

    # Initialize redis
    init_redis()

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    session.init_app(app)

    # Initialize Celery
    celery_app.conf.update(app.config)

    # Initialize models
    init_models(app)

    # Register blueprints
    from multilingual_webapp.app.chatbot import chatbot_blueprint

    app.register_blueprint(chatbot_blueprint)

    return app


def init_translation_model(app):
    try:
        with app.app_context():
            app.mmt_params = TranslationService.load_model()
        logger.info("MMTAFRICA model loaded successfully!")

    except Exception as e:
        logger.error(f"Failed to load MMTAFRICA model: {e}")
        raise


def init_speech_recognition_models(app):
    try:
        with app.app_context():
            app.whisper_base_model = whisper.load_model("base")

            # app.whisper_yoruba_pipeline = pipeline(
            # #     "automatic-speech-recognition", model="neoform-ai/whisper-medium-yoruba"
            # # )
            # app.whisper_yoruba_processor = AutoProcessor.from_pretrained(
            #     "neoform-ai/whisper-medium-yoruba"
            # )
            # app.whisper_yoruba_model = AutoModelForSpeechSeq2Seq.from_pretrained(
            #     "neoform-ai/whisper-medium-yoruba"
            # )
            # # app.whisper_fon_pipeline = pipeline(
            # #     "automatic-speech-recognition", model="chrisjay/fonxlsr"
            # # )
            # app.whisper_fon_processor = AutoProcessor.from_pretrained(
            #     "chrisjay/fonxlsr"
            # )
            # app.whisper_fon_model = AutoModelForCTC.from_pretrained("chrisjay/fonxlsr")
        logger.info("Speech recognition models loaded successfully!")

    except Exception as e:
        logger.error(f"Failed to load speech recognition models: {e}")
        raise


def init_llm(app):
    try:
        with app.app_context():
            app.llava_processor = LlavaNextProcessor.from_pretrained(
                "llava-hf/llava-v1.6-mistral-7b-hf"
            )
            app.llava_model = LlavaNextForConditionalGeneration.from_pretrained(
                "llava-hf/llava-v1.6-mistral-7b-hf",
                torch_dtype=torch.float16,
                low_cpu_mem_usage=True,
            )
            device = "cuda" if torch.cuda.is_available() else "cpu"
            if device == "cuda":
                app.llava_model.to("cuda")
        logger.info("LLM model loaded successfully!")

    except Exception as e:
        logger.error(f"Failed to load LLM: {e}")
        raise


def init_sentence_embedding_model(app):
    try:
        with app.app_context():
            app.sentence_embedding_model = SentenceTransformer("all-mpnet-base-v2")
        logger.info("sentence embedding model loaded successfully!")

    except Exception as e:
        logger.error(f"Failed to load sentence embedding model: {e}")
        raise


def init_image_recognition_model(app):
    try:
        with app.app_context():
            app.image_recognition_model = hub.load(
                "https://tfhub.dev/google/imagenet/mobilenet_v2_100_224/classification/5"
            )
        logger.info("image recognition model loaded successfully!")

    except Exception as e:
        logger.error(f"Failed to load image recognition model: {e}")
        raise


def init_models(app):
    # Initialize sentence embedding model
    init_sentence_embedding_model(app)

    # Initialize image recognition model
    init_image_recognition_model(app)

    # Initialize LLL
    init_llm(app)

    # Initialize speech recognition models
    init_speech_recognition_models(app)

    # Initialize translation model
    init_translation_model(app)


@retry_on_exception(
    retries=3,
    delay=5,
    exceptions=(redis.exceptions.ConnectionError, redis.exceptions.TimeoutError),
)
def init_redis(app):
    client = redis.Redis.from_url(app.config["REDIS_URL"])
    client.ping()

    if not client:
        logger.warning(
            "Falling back to filesystem sessions due to Redis connection issues."
        )
        app.config["SESSION_TYPE"] = "filesystem"
    else:
        app.config["SESSION_TYPE"] = "redis"
        app.config["SESSION_REDIS"] = client
    return client
