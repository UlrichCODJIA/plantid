import operator
import sys
import time
import traceback

import nltk
import torch
import whisper
from app.chat.utils.translation.translation import TranslationService
from app.database import initialize_db
from app.extensions import (
    anthropic_manager,
    celery_manager,
    jwt,
    knowledge_graph,
    logger,
    redis_manager,
    session,
    swagger,
)
from app.metrics import log_latency, log_request
from flask import Flask, request
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForCTC, AutoModelForSpeechSeq2Seq, AutoProcessor


def log_error(e, function_name):
    logger.error(f"Error in {function_name}: {e}")
    exc_type, exc_value, exc_traceback = sys.exc_info()
    logger.error(f"Error Type: {exc_type.__name__}")
    logger.error(f"Error Message: {str(e)}")
    tb = traceback.extract_tb(exc_traceback)
    filename, line_number, func_name, text = tb[-1]
    logger.error(f"File: {filename}")
    logger.error(f"Line Number: {line_number}")
    logger.error(f"Function: {func_name}")
    logger.error(f"Code: {text}")
    logger.error("\nFull Traceback:")
    traceback.print_exc()


def create_app(args):
    app = Flask(__name__)
    if args.environment in ["production", "make_celery"]:
        app.config.from_object("app.config.ProdConfig")
    elif args.environment == "testing":
        app.config.from_object("app.config.TestConfig")
    else:
        app.config.from_object("app.config.DevConfig")

    # Initialize extensions
    redis_manager.init_app(app, init_limiter=True)
    celery_manager.init_app(app)
    anthropic_manager.init_app(app)

    if not args.environment == "make_celery":
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

        # Initialize remaining extensions
        app.mongodb_client = initialize_db(app)
        jwt.init_app(app)
        session.init_app(app)
        swagger.init_app(app)
        knowledge_graph.init_app(app)

        # start_metrics_server()

        # Initialize models
        init_models(app)

        # Download nltk data
        nltk.download("punkt")
        nltk.download("stopwords")

        # Register blueprints
        from app.api.chatbot import chatbot_blueprint

        app.register_blueprint(chatbot_blueprint)

        @app.cli.command()
        def routes():
            "Display registered routes"
            rules = []
            for rule in app.url_map.iter_rules():
                methods = ",".join(sorted(rule.methods))
                rules.append((rule.endpoint, methods, str(rule)))

            sort_by_rule = operator.itemgetter(2)
            for endpoint, methods, rule in sorted(rules, key=sort_by_rule):
                route = "{:50s} {:25s} {}".format(endpoint, methods, rule)
                print(route)

    else:
        init_speech_recognition_models(app)

    return app


def init_translation_model(app):
    try:
        device = "gpu" if torch.cuda.is_available() else "cpu"
        with app.app_context():
            app.mmt_params = TranslationService.load_model(device)
        logger.info("MMTAFRICA model loaded successfully!")

    except Exception as e:
        log_error(e, "init_translation_model")
        raise


def init_speech_recognition_models(app):
    try:
        with app.app_context():
            app.whisper_base_model = whisper.load_model("base")

            app.whisper_yoruba_processor = AutoProcessor.from_pretrained("neoform-ai/whisper-medium-yoruba")
            app.whisper_yoruba_model = AutoModelForSpeechSeq2Seq.from_pretrained("neoform-ai/whisper-medium-yoruba")

            app.whisper_fon_processor = AutoProcessor.from_pretrained("chrisjay/fonxlsr")
            app.whisper_fon_model = AutoModelForCTC.from_pretrained("chrisjay/fonxlsr")
        logger.info("Speech recognition models loaded successfully!")

    except Exception as e:
        log_error(e, "init_speech_recognition_models")
        raise


def init_sentence_embedding_model(app):
    try:
        with app.app_context():
            app.sentence_embedding_model = SentenceTransformer("all-mpnet-base-v2")
        logger.info("sentence embedding model loaded successfully!")

    except Exception as e:
        log_error(e, "init_sentence_embedding_model")
        raise


def init_models(app):
    # Initialize sentence embedding model
    init_sentence_embedding_model(app)

    # Initialize speech recognition models
    init_speech_recognition_models(app)

    # Initialize translation model
    init_translation_model(app)
