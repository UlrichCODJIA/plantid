import logging
from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from multilingual_webapp.app.chatbot import chatbot_blueprint
from multilingual_webapp.app.chatbot.database import save_conversation
from multilingual_webapp.app.chatbot.dialogue_management import manage_dialogue
from multilingual_webapp.app.chatbot.error_handling import handle_error
from multilingual_webapp.app.chatbot.input_processing import process_input
from multilingual_webapp.app.chatbot.user_auth import authenticate_user
from multilingual_webapp.app.microservice_token import MicroserviceToken
from multilingual_webapp.app.tasks.tasks import generate_image_task
from multilingual_webapp.logger import configure_logger

logger = configure_logger(log_level=logging.DEBUG, log_file="logs/chat.log")

microservice_token = MicroserviceToken()


# Image status route
@chatbot_blueprint.route("/image-status/<task_id>")
@jwt_required()
def image_status(task_id):
    task = generate_image_task.AsyncResult(task_id)
    if task.state == "SUCCESS":
        return jsonify({"status": task.state, "image_url": task.get()})
    else:
        return jsonify({"status": task.state})


@chatbot_blueprint.route("/", methods=["POST"])
@jwt_required()
def chat():
    try:
        user_id = get_jwt_identity()
        user = authenticate_user(user_id)
        if not user:
            return handle_error("Unauthorized access", 403)

        language = request.form.get("language", user.language_preference)

        audio_file = request.files.get("audio")
        text_input = request.form.get("text")
        image_url = request.form.get("image_url")
        image_file = request.files.get("image")

        if (
            sum([bool(audio_file), bool(text_input), bool(image_url), bool(image_file)])
            > 1
        ):
            return handle_error("Please provide only one type of input", 400)

        inputs, translated_text, temp_file_path = process_input(
            audio_file, text_input, image_url, image_file, language
        )

        translated_response, new_state, image_task_id = manage_dialogue(
            user.id, translated_text, inputs, language
        )

        save_conversation(
            user.id,
            translated_text if text_input or audio_file else "<image>",
            translated_response,
            language,
            user.language_preference,
            new_state,
            temp_file_path if image_file or image_url else None,
        )

        response_data = {"response": translated_response}

        if image_task_id:
            response_data["image_task_id"] = image_task_id

        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Error: {e}")
        return handle_error("An error occurred. Please try again later.", 500)
