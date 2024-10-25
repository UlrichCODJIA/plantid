import re
import sys
import time
import traceback
from typing import List

from app.auth.user_auth import AuthResponseStatus, UserAuthenticator
from app.chat.error_handling import handle_error, handle_validation_error
from app.chat.input_processing import process_input
from app.chat.schemas.conversation import CreateConversationSchema, UpdateConversationSchema
from app.chat.utils.translation.translation import TranslationService
from app.extensions import anthropic_manager, chat_logger, redis_manager
from app.models.Conversation import Conversation
from app.models.Message import Message
from app.utils.nlp_utils import enhance_response_with_plant_info
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from mongoengine import Q
from redis import RedisError

chatbot_blueprint = Blueprint("chatbot", __name__, url_prefix="/api/v1")

redis_client = redis_manager.get_redis_client()

limiter = redis_manager.get_limiter()


def log_error(e, function_name):
    chat_logger.error(f"Error in {function_name}: {e}")
    exc_type, exc_value, exc_traceback = sys.exc_info()
    chat_logger.error(f"Error Type: {exc_type.__name__}")
    chat_logger.error(f"Error Message: {str(e)}")
    tb = traceback.extract_tb(exc_traceback)
    filename, line_number, func_name, text = tb[-1]
    chat_logger.error(f"File: {filename}")
    chat_logger.error(f"Line Number: {line_number}")
    chat_logger.error(f"Function: {func_name}")
    chat_logger.error(f"Code: {text}")
    chat_logger.error("\nFull Traceback:")
    traceback.print_exc()


@chatbot_blueprint.route("/conversations/<string:conversation_id>", methods=["GET"])
@jwt_required()
def get_conversation_by_id(conversation_id):
    try:
        user_id = get_jwt_identity()
        authenticator = UserAuthenticator()
        response = authenticator.authenticate_user(user_id)
        if not response.status == AuthResponseStatus.SUCCESS:
            return handle_error("Unauthorized access", 403)

        try:
            hash_key = f"conversation:{conversation_id}"
            conversation_data = redis_client.hgetall(hash_key)
            if not conversation_data:
                conversation = Conversation.objects(Q(id=conversation_id) & Q(user_id=user_id)).first()
                if conversation:
                    redis_client.hmset(
                        f"conversation:{conversation_id}",
                        {"data": conversation.to_json(), "last_updated": int(time.time())},
                    )
                    redis_client.expire(f"conversation:{conversation_id}", 3600)  # Expire after 1 hour
                    response = conversation.to_dict()
                else:
                    return handle_error("Conversation not found", 404)
            else:
                decoded_data = {k.decode("utf-8"): v.decode("utf-8") for k, v in conversation_data.items()}
                response = Conversation.from_json(decoded_data["data"]).to_dict()
                print(response)
        except RedisError as e:
            print(f"Redis error: {e}")
            # Fallback to database if Redis fails
            conversation = Conversation.objects(Q(id=conversation_id) & Q(user_id=user_id)).first()
            if not conversation:
                return handle_error("Conversation not found", 404)
            response = conversation.to_dict()

        # messages_data = [
        #     {k: v for k, v in message.to_dict().items() if k != "translated_text"} for message in conversation.messages
        # ]
        return jsonify(response), 200

    except Exception as e:
        log_error(e, "get_conversation_by_id")
        return handle_error(
            "An error occurred while retrieving the conversation. Please try again later.",
            500,
        )


def is_user_throttled(user_id):
    key = f"user_throttle:{user_id}"
    count = redis_client.incr(key)
    if count == 1:
        redis_client.expire(key, 60)
    return count > 100


@chatbot_blueprint.route(
    "/conversations",
    defaults={"conversation_id": None},
    methods=["POST"],
)
@chatbot_blueprint.route(
    "/conversations/<string:conversation_id>",
    methods=["POST"],
)
@jwt_required()
@limiter.limit("30 per minute")
def chat(conversation_id):
    new_chat = False
    try:
        user_id = get_jwt_identity()
        authenticator = UserAuthenticator()
        response = authenticator.authenticate_user(user_id)
        if not response.status == AuthResponseStatus.SUCCESS:
            return handle_error("Unauthorized access", 403)

        user = response.user

        audio_file = request.files.get("audio_data")
        print("request is: ", request)
        print("audio_file is: ", audio_file)
        user_message = request.form.get("text")

        if user_message and audio_file:
            return handle_error("Please provide only one type of input", 400)

        if conversation_id:
            try:
                hash_key = f"conversation:{conversation_id}"
                conversation_data = redis_client.hgetall(hash_key)

                if not conversation_data:
                    conversation = Conversation.objects(Q(id=conversation_id) & Q(user_id=user_id)).first()
                    if conversation:
                        redis_client.hmset(
                            f"conversation:{conversation_id}",
                            {"data": conversation.to_json(), "last_updated": int(time.time())},
                        )
                        redis_client.expire(f"conversation:{conversation_id}", 3600)  # Expire after 1 hour
                    else:
                        return handle_error("Conversation not found", 404)
                else:
                    decoded_data = {k.decode("utf-8"): v.decode("utf-8") for k, v in conversation_data.items()}
                    conversation = Conversation.from_json(decoded_data["data"])
            except RedisError as e:
                print(f"Redis error: {e}")
                # Fallback to database if Redis fails
                conversation = Conversation.objects(Q(id=conversation_id) & Q(user_id=user_id)).first()
                if not conversation:
                    return handle_error("Conversation not found", 404)
        else:
            new_chat = True
            try:
                if is_user_throttled(user_id):
                    return handle_error("Too many requests. Please try again later.", 429)
                data = {"user_id": user_id, "title": "chat"}
                schema = CreateConversationSchema()
                errors = schema.validate(data)
                if errors:
                    return handle_validation_error(errors)
                conversation = Conversation(**data)
                conversation.save()
                if bool(audio_file) + bool(user_message) < 1:
                    return jsonify(conversation.to_dict()), 201
            except Exception as e:
                log_error(e, "chat")
                return handle_error(
                    "An error occurred while creating the conversation. Please try again later.",
                    500,
                )

        user_message_obj = Message(
            conversation_id=conversation,
            sender="user",
        )
        bot_message_obj = Message(
            conversation_id=conversation,
            sender="bot",
        )

        detected_language = request.form.get("language", user.language_preference)

        context = prepare_chat_context(user)

        translated_text, audio_file_url = process_input(audio_file, user_message, detected_language, user_id)

        if not translated_text:
            return handle_error("Failed to process input", 400)

        print("translated text is: ", translated_text)

        response = anthropic_manager.generate_chat(
            context, translated_text, model="claude-3-opus-20240229", max_tokens=2048, temperature=0.9
        )

        print("first response is: ", response)

        enhanced_response, processed_response = process_chat_response(response, detected_language)

        print("enhanced response is: ", enhanced_response)
        print("processed response is: ", processed_response)

        message_fields = {
            "text": user_message,
            "audio_data": audio_file_url,
            "translated_text": translated_text,
        }

        bot_message_fields = {
            "text": processed_response,
            "translated_text": enhanced_response,
            # "audio_data": audio_file_url,
        }

        for attr, message_field in message_fields.items():
            if message_field:
                setattr(user_message_obj, attr, message_field)
        user_message_obj.save()

        for attr, field in bot_message_fields.items():
            if field:
                setattr(bot_message_obj, attr, field)
        bot_message_obj.save()

        conversation.update(
            set__user_id=user.id,
            set__title=generate_title([message for message in Message.objects(conversation_id=conversation.id)]),
            set__input_language=detected_language,
            set__output_language=user.language_preference,
            __raw__={
                "$addToSet": {"messages": {"$each": [message.pk for message in [user_message_obj, bot_message_obj]]}}
            },
        )

        conversation.reload()

        # Update Redis cache
        try:
            redis_client.hmset(
                f"conversation:{conversation.id}", {"data": conversation.to_json(), "last_updated": int(time.time())}
            )
            redis_client.expire(f"conversation:{conversation.id}", 3600)  # Expire after 1 hour
        except RedisError as e:
            print(f"Redis error while updating cache: {e}")

        if new_chat:
            response_data = {"conversation_id": conversation.to_dict()["id"]}
        else:
            response_data = {"response": processed_response}

        return jsonify(response_data)

    except Exception as e:
        log_error(e, "chat")
        return handle_error(
            "An error occurred while retrieving the conversation. Please try again later.",
            500,
        )


def prepare_chat_context(user):
    return f"""
    You are a specialized botanical expert focusing exclusively on African medicinal plants. Your knowledge encompasses traditional usage, scientific research, preparation methods, and safety considerations for medicinal plants native to Africa. The user's expertise level is {user.expertise_level}. Your task is to respond to queries about African medicinal plants, providing accurate and helpful information while adhering to the following guidelines:

    1. Only respond about African plants and their medicinal uses. Do not provide information about plants from other regions or non-medicinal uses of African plants.

    2. If asked about non-African plants or non-medicinal uses, politely redirect the conversation back to African medicinal plants. For example: "I apologize, but I specialize in African medicinal plants. Would you like information about any African plants with similar medicinal properties?"

    3. Ensure all information provided is accurate and based on reliable sources. Include references to scientific studies when possible.

    4. Always include appropriate cautionary advice about medical usage. Remind users to consult with healthcare professionals before using any medicinal plants.

    5. Provide information on traditional usage, but also include any available scientific research that supports or contradicts these uses.

    6. When discussing preparation methods, be clear and specific about the parts of the plant used, dosage, and method of administration.

    7. If there are known side effects or potential interactions with medications, make sure to mention these.

    8. If you're unsure about any aspect of the plant or its uses, clearly state that the information is limited or uncertain.

    Remember to always prioritize safety and accuracy in your responses.
    """


def process_chat_response(response_text, detected_language):
    enhanced_response = enhance_response_with_plant_info(response_text)

    if detected_language != "English":
        preprocessed_sentences = process_text_for_translation(enhanced_response, normalize_whitespace=True)
        translated_response = TranslationService.get_translation(
            source_lang="English", target_lang=detected_language, source_text=preprocessed_sentences
        )
    else:
        translated_response = enhanced_response

    return enhanced_response, translated_response


def process_text_for_translation(text: str, normalize_whitespace: bool = False) -> str:
    text = text.encode("utf-8").decode("unicode_escape")
    text = text.replace("\r\n", "\n")
    if normalize_whitespace:
        lines = [line.strip() for line in text.split("\n")]
        text = "\n".join(lines)
        text = text.replace("\n\n\n", "\n\n")
        text = text.strip()
    return text


def generate_title(messages: List[Message]) -> str:
    message_list = [
        {
            "role": "human" if msg.to_dict()["sender"] == "user" else "assistant",
            "content": msg.to_dict()["translated_text"],
        }
        for msg in messages
    ]
    conversation_context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in message_list])

    content = f"""
    Based on the following conversation, generate a concise and meaningful title that captures the main topic or theme. The title should be no more than 10 words long.

    Conversation:
    {conversation_context}

    Title:
    """

    response = anthropic_manager.generate_chat(
        content=content, model="claude-3-haiku-20240307", max_tokens=20, temperature=0.7, top_p=1
    )

    return response


@chatbot_blueprint.route("/conversations/<int:conversation_id>", methods=["PUT"])
@jwt_required()
def update_conversation_title(conversation_id):
    try:
        data = request.get_json()
        schema = UpdateConversationSchema()
        errors = schema.validate(data)
        user_id = get_jwt_identity()
        if errors:
            return handle_validation_error(errors)
        conversation = Conversation.objects(id=conversation_id).first()
        if not conversation.user_id == user_id:
            return handle_error("Unauthorized access", 403)
        if not conversation:
            return handle_error("Conversation not found", 404)
        conversation.update(**{f"set__{key}": value for key, value in data.items()})
        return jsonify(conversation.to_dict()), 200
    except Exception as e:
        log_error(e, "update_conversation_title")
        return handle_error("An error occurred while updating the conversation", 500)


@chatbot_blueprint.route("/conversations/<int:conversation_id>", methods=["DELETE"])
@jwt_required()
def delete_conversation(conversation_id):
    try:
        user_id = get_jwt_identity()
        conversation = Conversation.objects(id=conversation_id).first()
        if not conversation.user_id == user_id:
            return handle_error("Unauthorized access", 403)
        if conversation is None:
            return jsonify({"error": "Conversation not found"}), 404
        conversation.delete()
        return jsonify({"message": "Conversation deleted successfully"}), 200
    except Exception as e:
        log_error(e, "delete_conversation")
        return handle_error("An error occurred while deleting the conversation", 500)


@chatbot_blueprint.route("/conversations", methods=["GET"])
@jwt_required()
def list_conversations():
    try:
        user_id = get_jwt_identity()
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))
        dialogue_state = request.args.get("dialogue_state")
        sort_field = request.args.get("sort_field", "timestamp")
        sort_order = request.args.get("sort_order", "desc")

        query = Conversation.objects(user_id=user_id)

        if dialogue_state:
            query = query.filter(dialogue_state=dialogue_state)

        if sort_field not in ["timestamp", "dialogue_state"]:
            sort_field = "timestamp"

        if sort_order == "asc":
            conversations = query.order_by(f"+{sort_field}").skip((page - 1) * per_page).limit(per_page)
        else:
            conversations = query.order_by(f"-{sort_field}").skip((page - 1) * per_page).limit(per_page)

        total_count = query.count()

        return (
            jsonify(
                {
                    "conversations": [conv.to_dict() for conv in conversations],
                    "page": page,
                    "per_page": per_page,
                    "total_count": total_count,
                }
            ),
            200,
        )
    except Exception as e:
        log_error(e, "list_conversations")
        return handle_error("An error occurred while retrieving the conversations", 500)
