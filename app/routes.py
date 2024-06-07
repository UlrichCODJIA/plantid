from flask import Blueprint
from multilingual_webapp.app.chatbot.routes import chatbot_blueprint


routes_blueprint = Blueprint("routes", __name__)
routes_blueprint.register_blueprint(chatbot_blueprint, url_prefix="/chat")
