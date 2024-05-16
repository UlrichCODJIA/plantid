from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.settings')

    # Initialize and register blueprints, extensions, etc.
    from app.chatbot import chatbot_blueprint
    app.register_blueprint(chatbot_blueprint, url_prefix='/chatbot')

    from app.image_generation import image_generation_blueprint
    app.register_blueprint(image_generation_blueprint, url_prefix='/images')

    from app.speech_recognition import speech_recognition_blueprint
    app.register_blueprint(speech_recognition_blueprint, url_prefix='/speech')

    return app