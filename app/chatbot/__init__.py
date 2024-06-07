from flask import Blueprint

chatbot_blueprint = Blueprint("chatbot", __name__)

from multilingual_webapp.app.chatbot import routes
