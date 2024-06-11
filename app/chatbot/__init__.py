from flask import Blueprint

chatbot_blueprint = Blueprint("chatbot", __name__, url_prefix="/api/v1")
