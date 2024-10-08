from flask import jsonify
from app import chat_logger
from app.chatbot.dialogue_management import generate_title, manage_dialogue
from app.chatbot.input_processing import process_input
from app.chatbot.error_handling import handle_error
from app.extensions import redis_manager

redis_client = redis_manager.get_redis_client()


# Security: Allowed extensions for image files
ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
}


def is_user_throttled(user_id):
    key = f"user_throttle:{user_id}"
    count = redis_client.incr(key)
    if count == 1:
        redis_client.expire(key, 60)
    return count > 100


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def handle_post_request(
    session,
    user,
    conversation,
    user_message,
    bot_message,
    language,
    audio_file,
    text_input,
    image_file,
    new_chat,
):
    try:

        if audio_file and text_input:
            return handle_error("Please provide only one type of input", 400)

        if image_file and not allowed_file(image_file.filename):
            return handle_error(
                "Invalid file type. Only PNG, JPG and JPEG are allowed.", 400
            )

        bot_message.text = text_input

        return handle_chat(
            session,
            user,
            audio_file,
            text_input,
            image_file,
            language,
            conversation,
            user_message,
            bot_message,
            new_chat,
        )

    except Exception as e:
        chat_logger.error(f"Error in handle_post_request: {e}")
        return handle_error(
            "An error occurred while processing the request. Please try again later.",
            500,
        )


def handle_chat(
    session,
    user,
    audio_file,
    text_input,
    image_file,
    language,
    conversation,
    user_message,
    bot_message,
    new_chat,
):
    try:
        inputs, translated_text, image_file_url, audio_file_url = process_input(
            audio_file, text_input, image_file, language, conversation.user_id
        )

        message_fields = {
            "text": text_input,
            "image_url": image_file_url,
            "audio_data": audio_file_url,
        }

        for attr, message_field in message_fields.items():
            if message_field:
                setattr(user_message, attr, message_field)
        user_message.save()

        translated_response, new_state, image_task_id, bot_message_fields = (
            manage_dialogue(session, translated_text, inputs, language, conversation)
        )

        for attr, field in bot_message_fields.items():
            if field:
                setattr(bot_message, attr, field)
        bot_message.save()

        conversation.update(
            set__user_id=user.id,
            set__title=generate_title(translated_text),
            set__input_language=language,
            set__output_language=user.language_preference,
            set__dialogue_state=new_state,
            set__image_task_id=image_task_id,
        )

        conversation.messages.extend([user_message, bot_message])
        conversation.save()

        if new_chat:
            response_data = {"conversation_id": conversation.to_dict()["id"]}
        else:
            response_data = {"response": translated_response}

        if image_task_id:
            response_data["image_task_id"] = image_task_id

        return jsonify(response_data)

    except Exception as e:
        chat_logger.error(f"Error in handle_chat: {e}")
        return handle_error(
            "An error occurred while processing the chat. Please try again later.", 500
        )
