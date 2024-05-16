from flask import Blueprint, request, jsonify
import ollama

from utils.translation import TranslationService

chatbot_blueprint = Blueprint("chatbot", __name__)


@chatbot_blueprint.route("/chat", methods=["POST"])
def chat():
    user_input = request.json["input"]
    language = request.json["language"]
    translation_service_obj = TranslationService()

    # Translate user input to English
    translated_input = translation_service_obj.get_translation(
        source_language=language, target_language="en", source_sentence=user_input
    )

    # Get chatbot response using Ollama API
    response = ollama.chat(
        model="mistral",
        messages=[
            {
                "role": "user",
                "content": translated_input,
            },
        ],
    )

    # Extract the chatbot's response from the API response
    chatbot_response = response["message"]["content"]

    # Translate response back to user's language
    translated_response = translation_service_obj.get_translation(
        source_language="en", target_language=language, source_sentence=chatbot_response
    )

    return jsonify({"response": translated_response})
