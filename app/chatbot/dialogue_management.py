from flask import current_app, jsonify, request
from sentence_transformers import util

from multilingual_webapp.app.chatbot.llava_response import generate_response
from multilingual_webapp.app.chatbot.response_translation import translate_response
from multilingual_webapp.app.chatbot.sentiment_analysis import analyze_sentiment
from multilingual_webapp.app.models.models import Conversation
from multilingual_webapp.app.tasks.tasks import generate_image_task


def get_current_state(user_id):
    last_conversation = (
        Conversation.query.filter_by(user_id=user_id)
        .order_by(Conversation.timestamp.desc())
        .first()
    )
    return last_conversation.dialogue_state if last_conversation else "greeting"


def handle_greeting_state(sentiment):
    if sentiment >= 0:
        return "Hello! How can I help you today?", "conversing"
    else:
        return (
            "Hello, it seems like you're having a tough day. What's going on?",
            "conversing",
        )


def handle_confirming_image_generation_state(translated_text):
    if any(
        keyword in translated_text.lower()
        for keyword in ["yes", "sure", "okay", "yeah"]
    ):
        image_task = generate_image_task.delay(translated_text)
        return (
            "Okay, I'm generating an image for you. You can check the status with the provided task ID.",
            "generating_image",
        )
    else:
        return (
            "Alright, let's continue chatting then. What else is on your mind?",
            "conversing",
        )


def handle_generating_image_state(image_task_id):
    image_task = generate_image_task.AsyncResult(image_task_id)

    if image_task.state == "SUCCESS":
        image_url = image_task.get()
        return f"Here's the generated image: {image_url}", "confirming"
    elif image_task.state in ["PENDING", "STARTED"]:
        return (
            "The image is still being generated. Please wait a bit.",
            "generating_image",
        )
    elif image_task.state == "FAILURE":
        return (
            "Sorry, there was an error generating the image. Please try again later.",
            "conversing",
        )
    else:
        return (
            "I'm not sure what the status of the image generation is. Please try again later.",
            "conversing",
        )


def handle_confirming_state(translated_text, sentiment):
    if any(keyword in translated_text.lower() for keyword in ["yes", "sure", "please"]):
        return "Okay, what else can I do for you?", "conversing"
    else:
        if sentiment >= 0:
            return "Alright, have a great day!", "end"
        else:
            return "Okay, I hope you feel better soon!", "end"


def handle_end_state():
    return "Goodbye!", "end"


def check_image_intent(translated_text):
    image_generation_phrases = [
        "Can you create an image of",
        "I'd like to see a picture of",
        "Generate an image showing",
        "Please make an image that depicts",
        "Could you draw",
        "Can you paint",
        "I want to see a picture of",
        "Create a visual representation of",
        "Show me an image of",
        "Make me a picture of",
        "Imagine an image of",
        "Visualize and create an image of",
    ]

    response_embedding = current_app.sentence_embedding_model.encode(
        translated_text, convert_to_tensor=True
    )
    image_generation_embeddings = current_app.sentence_embedding_model.encode(
        image_generation_phrases, convert_to_tensor=True
    )
    cosine_scores = util.cos_sim(response_embedding, image_generation_embeddings)
    max_similarity = cosine_scores.max().item()
    similarity_threshold = 0.7  # Adjust as needed

    if max_similarity >= similarity_threshold:
        return True

    intent_prompt = (
        f"The user said: '{translated_text}'. Does the user want to generate an image?"
    )
    intent_inputs = current_app.llava_processor(
        text=intent_prompt, return_tensors="pt"
    ).to(current_app.llava_model.device)
    intent_generated_ids = current_app.llava_model.generate(
        **intent_inputs, max_new_tokens=10
    )
    intent_response = current_app.llava_processor.batch_decode(
        intent_generated_ids, skip_special_tokens=True
    )[0]

    return "yes" in intent_response.lower()


def should_transition_to_confirming(chatbot_response):
    confirmation_phrases = [
        "Is there anything else I can help you with?",
        "Do you have any other questions?",
        "Anything else I can assist you with today?",
    ]
    response_embedding = current_app.sentence_embedding_model.encode(
        chatbot_response, convert_to_tensor=True
    )
    confirmation_embeddings = current_app.sentence_embedding_model.encode(
        confirmation_phrases, convert_to_tensor=True
    )
    cosine_scores = util.cos_sim(response_embedding, confirmation_embeddings)
    max_similarity = cosine_scores.max().item()
    similarity_threshold = 0.8  # Adjust as needed
    if max_similarity >= similarity_threshold:
        return True

    consecutive_short_responses = request.session.get("consecutive_short_responses", 0)
    short_response_threshold = 3  # Adjust as needed
    short_response_length = 50  # Adjust as needed
    if len(chatbot_response) <= short_response_length:
        consecutive_short_responses += 1
    else:
        consecutive_short_responses = 0
    request.session["consecutive_short_responses"] = consecutive_short_responses
    if consecutive_short_responses >= short_response_threshold:
        return True

    return False


def manage_dialogue(user_id, translated_text, inputs, language):
    states = [
        "greeting",
        "conversing",
        "confirming_image_generation",
        "generating_image",
        "confirming",
        "end",
    ]

    image_task_id = None

    sentiment = analyze_sentiment(translated_text)

    last_conversation = (
        Conversation.query.filter_by(user_id=user_id)
        .order_by(Conversation.timestamp.desc())
        .first()
    )

    current_state = "greeting"
    if last_conversation:
        current_state = last_conversation.dialogue_state

    chatbot_response = None

    if current_state == "greeting":
        chatbot_response = (
            "Hello! How can I help you today?"
            if sentiment >= 0
            else "Hello, it seems like you're having a tough day. What's going on?"
        )
        new_state = "conversing"

    elif current_state in [
        "conversing",
        "asking_need",
        "getting_info",
        "providing_info",
    ]:
        check_image_intent_flag = (
            current_state == "conversing"
            and last_conversation.dialogue_state != "conversing"
        ) or (last_conversation and last_conversation.input_text != "<image>")
        if check_image_intent_flag:
            if check_image_intent(translated_text):
                chatbot_response = "What would you like me to generate an image of?"
                new_state = "confirming_image_generation"
            else:
                chatbot_response = generate_response(inputs)
                if should_transition_to_confirming(chatbot_response):
                    new_state = "confirming"
                else:
                    new_state = "conversing"
        else:
            chatbot_response = generate_response(inputs)
            if should_transition_to_confirming(chatbot_response):
                new_state = "confirming"
            else:
                new_state = "conversing"

    elif current_state == "confirming_image_generation":
        if any(
            keyword in translated_text.lower()
            for keyword in ["yes", "sure", "okay", "yeah"]
        ):
            image_task = generate_image_task.delay(translated_text)
            chatbot_response = "Okay, I'm generating an image for you. You can check the status with the provided task ID."
            new_state = "generating_image"
            image_task_id = image_task.id
        else:
            chatbot_response = (
                "Alright, let's continue chatting then. What else is on your mind?"
            )
            new_state = "conversing"

    elif current_state == "generating_image":
        image_task_id = request.form.get("image_task_id")
        if not image_task_id:
            return jsonify({"error": "Missing image_task_id parameter."}), 400

        image_task = generate_image_task.AsyncResult(image_task_id)

        if image_task.state == "SUCCESS":
            image_url = image_task.get()
            chatbot_response = f"Here's the generated image: {image_url}"
            new_state = "confirming"
        elif image_task.state in ["PENDING", "STARTED"]:
            chatbot_response = "The image is still being generated. Please wait a bit."
            new_state = "generating_image"
        elif image_task.state == "FAILURE":
            chatbot_response = "Sorry, there was an error generating the image. Please try again later."
            new_state = "conversing"
        else:
            chatbot_response = "I'm not sure what the status of the image generation is. Please try again later."
            new_state = "conversing"

    elif current_state == "confirming":
        if any(
            keyword in translated_text.lower() for keyword in ["yes", "sure", "please"]
        ):
            chatbot_response = "Okay, what else can I do for you?"
            new_state = "conversing"
        else:
            chatbot_response = (
                "Alright, have a great day!"
                if sentiment >= 0
                else "Okay, I hope you feel better soon!"
            )
            new_state = "end"

    elif current_state == "end":
        chatbot_response = "Goodbye!"
        new_state = "end"

    translated_response = translate_response(chatbot_response, language)

    return translated_response, new_state, image_task_id
