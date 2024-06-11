from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from mongoengine import Q

from app import chat_logger
from app.chatbot import chatbot_blueprint
from app.chatbot.error_handling import handle_error, handle_validation_error
from app.chatbot.user_auth import authenticate_user
from app.tasks.tasks import generate_image_task
from app.models.Conversation import Conversation
from app.models.Message import Message
from app.extensions import limiter, redis_manager
from app.schemas.conversation import CreateConversationSchema, UpdateConversationSchema
from app.services.chatbot_service import handle_post_request, is_user_throttled

redis_client = redis_manager.get_redis_client()


@chatbot_blueprint.route("/image-status/<task_id>")
@jwt_required()
def image_status(task_id):
    try:
        task = generate_image_task.AsyncResult(task_id)
        if task.state == "SUCCESS":
            return jsonify({"status": task.state, "image_url": task.get()})
        else:
            return jsonify({"status": task.state})
    except Exception as e:
        chat_logger.error(f"Error in image_status: {e}")
        return handle_error(
            "An error occurred while retrieving image status. Please try again later.",
            500,
        )


@chatbot_blueprint.route("/conversations/<int:conversation_id>", methods=["GET"])
@jwt_required()
def get_conversation_by_id(conversation_id):
    try:
        user_id = get_jwt_identity()
        user = authenticate_user(user_id)
        if not user:
            return handle_error("Unauthorized access", 403)

        conversation = redis_client.get(f"conversation:{conversation_id}")
        if not conversation:
            conversation = Conversation.objects(
                Q(id=conversation_id) & Q(user_id=user_id)
            ).first()
            if conversation:
                redis_client.set(
                    f"conversation:{conversation_id}", conversation.to_json()
                )
            else:
                return handle_error("Conversation not found", 404)
        else:
            conversation = Conversation.from_json(conversation)

        messages_data = [message.to_dict() for message in conversation.messages]
        return jsonify(messages=messages_data), 200

    except Exception as e:
        chat_logger.error(f"Error in get_conversation: {e}")
        return handle_error(
            "An error occurred while retrieving the conversation. Please try again later.",
            500,
        )


@chatbot_blueprint.route(
    "/conversations/<int:conversation_id>",
    defaults={"conversation_id": None},
    methods=["POST"],
)
@jwt_required()
@limiter.limit("40/minute")
def chat(conversation_id):
    try:
        user_id = get_jwt_identity()
        user = authenticate_user(user_id)
        if not user:
            return handle_error("Unauthorized access", 403)

        if conversation_id:
            conversation = redis_client.get(f"conversation:{conversation_id}")
            if conversation is None:
                conversation = Conversation.objects(
                    Q(id=conversation_id) & Q(user_id=user_id)
                ).first()
                if conversation:
                    redis_client.set(
                        f"conversation:{conversation_id}", conversation.to_json()
                    )
                else:
                    return handle_error("Conversation not found", 404)
            else:
                conversation = Conversation.from_json(conversation)
        else:
            try:
                if is_user_throttled(user_id):
                    return handle_error(
                        "Too many requests. Please try again later.", 429
                    )
                data = {"user_id": user_id, "title": "chat"}
                schema = CreateConversationSchema()
                errors = schema.validate(data)
                if errors:
                    return handle_validation_error(errors)

                conversation = Conversation(**data)
                conversation.save()
                return jsonify(conversation.to_dict()), 201
            except Exception as e:
                chat_logger.error(f"Error in create_conversation: {e}")
                return handle_error(
                    "An error occurred while creating the conversation. Please try again later.",
                    500,
                )

        if conversation.image_task_status in ["STARTED", "PENDING"]:
            return handle_error(
                "Wait till image is generated.",
                403,
            )
        user_message = Message(
            conversation_id=conversation,
            sender="user",
        )
        bot_message = Message(
            conversation_id=conversation,
            sender="bot",
        )
        return handle_post_request(
            request, user, conversation, user_message, bot_message
        )

    except Exception as e:
        chat_logger.error(f"Error in get_conversation: {e}")
        return handle_error(
            "An error occurred while retrieving the conversation. Please try again later.",
            500,
        )


@chatbot_blueprint.route("/conversations/<int:conversation_id>", methods=["PUT"])
@jwt_required()
def update_conversation_title(conversation_id):
    try:
        data = request.get_json()
        schema = UpdateConversationSchema()
        errors = schema.validate(data)
        if errors:
            return handle_validation_error(errors)
        conversation = Conversation.objects(id=conversation_id).first()
        if not conversation:
            return handle_error("Conversation not found", 404)
        conversation.update(**{f"set__{key}": value for key, value in data.items()})
        return jsonify(conversation.to_dict()), 200
    except Exception as e:
        chat_logger.error(f"Error in update_conversation: {e}")
        return handle_error("An error occurred while updating the conversation", 500)


@chatbot_blueprint.route("/conversations/<int:conversation_id>", methods=["DELETE"])
@jwt_required()
def delete_conversation(conversation_id):
    try:
        conversation = Conversation.objects(id=conversation_id).first()
        if conversation is None:
            return jsonify({"error": "Conversation not found"}), 404
        conversation.delete()
        return jsonify({"message": "Conversation deleted successfully"}), 200
    except Exception as e:
        chat_logger.error(f"Error in delete_conversation: {e}")
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

        # Validate the sort field to prevent injection attacks
        if sort_field not in ["timestamp", "dialogue_state"]:
            sort_field = "timestamp"

        if sort_order == "asc":
            conversations = (
                query.order_by(f"+{sort_field}")
                .skip((page - 1) * per_page)
                .limit(per_page)
            )
        else:
            conversations = (
                query.order_by(f"-{sort_field}")
                .skip((page - 1) * per_page)
                .limit(per_page)
            )

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
        chat_logger.error(f"Error in list_conversations: {e}")
        return handle_error("An error occurred while retrieving the conversations", 500)
