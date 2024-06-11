from flask import current_app
from sentence_transformers import util
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

from app import chat_logger
from app.chatbot.llava_response import generate_response
from app.chatbot.response_translation import translate_response
from app.chatbot.sentiment_analysis import analyze_sentiment
from app.tasks.tasks import generate_image_task
from app.chatbot.error_handling import handle_error


IMAGE_GENERATION_PHRASES = [
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
IMAGE_GENERATION_SIMILARITY_THRESHOLD = 0.7
CONFIRMATION_PHRASES = [
    "Is there anything else I can help you with?",
    "Do you have any other questions?",
    "Anything else I can assist you with today?",
]
CONFIRMATION_SIMILARITY_THRESHOLD = 0.8
SHORT_RESPONSE_THRESHOLD = 3
SHORT_RESPONSE_LENGTH = 50
DIALOGUE_STATES = {
    "greeting": "greeting",
    "conversing": "conversing",
    "confirming": "confirming",
    "generating_image": "generating_image",
    "end": "end",
}


def generate_title(translated_text):
    """
    Generate a title from the translated text by removing stop words and capitalizing the first word.

    Args:
        translated_text (str): The translated text to generate the title from.

    Returns:
        str: The generated title.
    """
    tokens = word_tokenize(translated_text)
    stop_words = set(stopwords.words("english"))
    filtered_tokens = [
        word.lower()
        for word in tokens
        if word.isalnum() and word.lower() not in stop_words
    ]
    title = " ".join(filtered_tokens)
    return title.capitalize()


def handle_greeting_state(sentiment):
    """
    Handle the greeting state based on the sentiment.

    Args:
        sentiment (float): The sentiment score.

    Returns:
        tuple: A tuple containing the response and the new state.
    """
    if sentiment >= 0:
        return "Hello! How can I help you today?", DIALOGUE_STATES["conversing"]
    else:
        return (
            "Hello, it seems like you're having a tough day. What's going on?",
            DIALOGUE_STATES["conversing"],
        )


def handle_confirming_image_generation_state(translated_text):
    """
    Handle the confirming image generation state based on the translated text.

    Args:
        translated_text (str): The translated text.

    Returns:
        tuple: A tuple containing the response, the new state, and the image task ID (if applicable).
    """
    image_task = generate_image_task.delay(translated_text)
    return (
        "Okay, I'm generating an image for you. You can check the status with the provided task ID.",
        DIALOGUE_STATES["generating_image"],
        image_task.id,
    )


def handle_generating_image_state(image_task_id, user_id):
    """
    Handle the generating image state based on the image task ID.

    Args:
        image_task_id (str): The ID of the image generation task.

    Returns:
        tuple: A tuple containing the response and the new state.
    """

    image_task = generate_image_task.AsyncResult(image_task_id)
    if image_task.state == "SUCCESS":
        try:
            image_file_url = image_task.get()
            return (
                f"Here's the generated image: {image_file_url}",
                image_file_url,
                DIALOGUE_STATES["confirming"],
            )
        except Exception as e:
            chat_logger.error(f"Error in process_input: {e}")
            return (
                "I'm not sure what the status of the image generation is. Please try again later.",
                None,
                DIALOGUE_STATES["conversing"],
            )
    elif image_task.state in ["PENDING", "STARTED"]:
        return (
            "The image is still being generated. Please wait a bit.",
            None,
            DIALOGUE_STATES["generating_image"],
        )
    elif image_task.state == "FAILURE":
        return (
            "Sorry, there was an error generating the image. Please try again later.",
            None,
            DIALOGUE_STATES["conversing"],
        )
    else:
        return (
            "I'm not sure what the status of the image generation is. Please try again later.",
            None,
            DIALOGUE_STATES["conversing"],
        )


def handle_confirming_state(translated_text, sentiment):
    """
    Handle the confirming state based on the translated text and sentiment.

    Args:
        translated_text (str): The translated text.
        sentiment (float): The sentiment score.

    Returns:
        tuple: A tuple containing the response and the new state.
    """
    if any(keyword in translated_text.lower() for keyword in ["yes", "sure", "please"]):
        return "Okay, what else can I do for you?", DIALOGUE_STATES["conversing"]
    else:
        return (
            "Alright, have a great day!"
            if sentiment >= 0
            else "Okay, I hope you feel better soon!"
        ), DIALOGUE_STATES["end"]


def handle_end_state():
    """
    Handle the end state.

    Returns:
        tuple: A tuple containing the response and the new state.
    """
    return "Goodbye!", DIALOGUE_STATES["end"]


def handle_default_state(req, inputs):
    """
    Handle the default state based on the translated text, sentiment, and inputs.

    Args:
        inputs (dict): The input data.

    Returns:
        tuple: A tuple containing the response and the new state.
    """
    chatbot_response = generate_response(inputs)
    if not chatbot_response:
        chatbot_response = (
            "I'm sorry, but I don't understand. Could you please rephrase your request?"
        )
    new_state = (
        DIALOGUE_STATES["confirming"]
        if should_transition_to_confirming(req, chatbot_response)
        else DIALOGUE_STATES["conversing"]
    )
    return chatbot_response, new_state


def check_image_intent(translated_text):
    """
    Check if the translated text indicates an intent to generate an image.

    Args:
        translated_text (str): The translated text.

    Returns:
        bool: True if the text indicates an image generation intent, False otherwise.
    """

    response_embedding = current_app.sentence_embedding_model.encode(
        translated_text, convert_to_tensor=True
    )
    image_generation_embeddings = current_app.sentence_embedding_model.encode(
        IMAGE_GENERATION_PHRASES, convert_to_tensor=True
    )
    cosine_scores = util.cos_sim(response_embedding, image_generation_embeddings)
    max_similarity = cosine_scores.max().item()
    similarity_threshold = IMAGE_GENERATION_SIMILARITY_THRESHOLD

    if max_similarity >= similarity_threshold:
        return True

    intent_prompt = f"""
    Please analyze the following statement and provide a simple "yes" or "no" answer:

    "The user said: '{translated_text}'. Does the user want to generate an image?"

    Your answer should only be "yes" or "no" based on whether the user's statement indicates a desire to generate an image.
    """
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


def should_transition_to_confirming(req, chatbot_response):
    """
    Check if the chatbot response indicates a transition to the confirming state.

    Args:
        chatbot_response (str): The chatbot response.

    Returns:
        bool: True if the response indicates a transition to the confirming state, False otherwise.
    """

    response_embedding = current_app.sentence_embedding_model.encode(
        chatbot_response, convert_to_tensor=True
    )
    confirmation_embeddings = current_app.sentence_embedding_model.encode(
        CONFIRMATION_PHRASES, convert_to_tensor=True
    )
    cosine_scores = util.cos_sim(response_embedding, confirmation_embeddings)
    max_similarity = cosine_scores.max().item()
    similarity_threshold = CONFIRMATION_SIMILARITY_THRESHOLD

    if max_similarity >= similarity_threshold:
        return True

    consecutive_short_responses = req.session.get("consecutive_short_responses", 0)
    short_response_threshold = SHORT_RESPONSE_THRESHOLD
    short_response_length = SHORT_RESPONSE_LENGTH

    if len(chatbot_response) <= short_response_length:
        consecutive_short_responses += 1
    else:
        consecutive_short_responses = 0

    req.session["consecutive_short_responses"] = consecutive_short_responses

    return consecutive_short_responses >= short_response_threshold


def manage_dialogue(req, translated_text, inputs, language, conversation):
    sentiment = analyze_sentiment(translated_text)
    current_state = conversation.dialogue_state
    intent = False
    image_task_id = None
    image_url = None

    if current_state == DIALOGUE_STATES["greeting"]:
        chatbot_response, new_state = handle_greeting_state(sentiment)
    elif current_state == DIALOGUE_STATES["conversing"]:
        intent = check_image_intent(translated_text)
        if intent:
            chatbot_response = "What would you like me to generate an image of?"
            new_state = "confirming_image_generation"
        else:
            chatbot_response, new_state = handle_default_state(req, inputs)
    elif current_state == "confirming_image_generation":
        chatbot_response, new_state, image_task_id = (
            handle_confirming_image_generation_state(translated_text)
        )
    elif current_state == DIALOGUE_STATES["generating_image"]:
        image_task_id = conversation.image_task_id
        if not image_task_id:
            return (
                handle_error(
                    {
                        "error": "An error occurred while processing the chat. Please try again later."
                    }
                ),
                500,
            )
        chatbot_response, image_url, new_state = handle_generating_image_state(
            image_task_id, conversation.user_id
        )
    elif current_state == DIALOGUE_STATES["confirming"]:
        chatbot_response, new_state = handle_confirming_state(
            translated_text, sentiment
        )
    elif current_state == DIALOGUE_STATES["end"]:
        chatbot_response, new_state = handle_end_state()
    else:
        chatbot_response, new_state = handle_default_state(req, inputs)

    translated_response = translate_response(chatbot_response, language)

    bot_message_fields = {
        "text": translated_response,
        "image_url": image_url,
        # "audio_data": audio_file_url,
    }

    return translated_response, new_state, sentiment, image_task_id, bot_message_fields
