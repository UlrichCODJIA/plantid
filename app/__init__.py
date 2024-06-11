import os

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import logging
from flask import Flask, request
import whisper
import nltk
import time

import torch
from logger import configure_logger
from sentence_transformers import SentenceTransformer
import tensorflow_hub as hub
from transformers import (
    # pipeline,
    LlavaNextProcessor,
    LlavaNextForConditionalGeneration,
    AutoProcessor,
    AutoModelForSpeechSeq2Seq,
    AutoModelForCTC,
)

from app.extensions import (
    jwt,
    session,
    celery_manager,
    redis_manager,
    swagger,
    limiter,
)
from app.metrics import log_latency, log_request, start_metrics_server
from app.database import initialize_db

logger = configure_logger(log_level=logging.DEBUG, log_file="logs/app.log")

chat_logger = configure_logger(log_level=logging.DEBUG, log_file="logs/chat.log")


def create_app(args):

    app = Flask(__name__)
    if args.environment == "production":
        app.config.from_object("app.config.ProdConfig")
    elif args.environment == "testing":
        app.config.from_object("app.config.TestConfig")
    else:
        app.config.from_object("app.config.DevConfig")

    # Initialize prometheus metrics
    @app.before_request
    def before_request():
        request.start_time = time.time()

    @app.after_request
    def after_request(response):
        latency = time.time() - request.start_time
        endpoint = request.endpoint
        log_request(endpoint)
        log_latency(endpoint, latency)
        return response

    # Initialize extensions
    redis_manager.init_app(app)
    initialize_db(app)
    jwt.init_app(app)
    session.init_app(app)
    celery_manager.init_app(app)
    swagger.init_app(app)
    limiter.init_app(app)

    start_metrics_server()

    # Initialize models
    init_models(app)

    # Download nltk data
    nltk.download("punkt")
    nltk.download("stopwords")

    # Register blueprints
    from app.chatbot import chatbot_blueprint

    app.register_blueprint(chatbot_blueprint)

    return app


def init_translation_model(app):
    try:
        device = "gpu" if torch.cuda.is_available() else "cpu"
        # with app.app_context():
        #     app.mmt_params = TranslationService.load_model(device)
        logger.info("MMTAFRICA model loaded successfully!")

    except Exception as e:
        logger.error(f"Failed to load MMTAFRICA model: {e}")
        raise


def init_speech_recognition_models(app):
    try:
        with app.app_context():
            app.whisper_base_model = whisper.load_model("base")

            # app.whisper_yoruba_pipeline = pipeline(
            #     "automatic-speech-recognition", model="neoform-ai/whisper-medium-yoruba"
            # )
            app.whisper_yoruba_processor = AutoProcessor.from_pretrained(
                "neoform-ai/whisper-medium-yoruba"
            )
            app.whisper_yoruba_model = AutoModelForSpeechSeq2Seq.from_pretrained(
                "neoform-ai/whisper-medium-yoruba"
            )
            # app.whisper_fon_pipeline = pipeline(
            #     "automatic-speech-recognition", model="chrisjay/fonxlsr"
            # )
            app.whisper_fon_processor = AutoProcessor.from_pretrained(
                "chrisjay/fonxlsr"
            )
            app.whisper_fon_model = AutoModelForCTC.from_pretrained("chrisjay/fonxlsr")
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
