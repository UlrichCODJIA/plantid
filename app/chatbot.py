from datetime import datetime, timedelta
import os
import logging
from flask import Blueprint, request, jsonify, current_app
import tempfile
import requests
import speech_recognition as sr
import pyttsx3
from celery import Celery
from utils.text_to_image import TextToImageGenerator
from utils.speech_recognition import transcribe_audio, transcribe_yoruba, transcribe_fon
from flask_jwt_extended import get_jwt_identity, jwt_required
from PIL import Image
import redis
from textblob import TextBlob
from sentence_transformers import util
from celery.schedules import crontab

from models.models import Conversation, User
from utils.translation import TranslationService
from logger import configure_logger

logger = configure_logger(log_level=logging.DEBUG, log_file="chatbot.log")

chatbot_blueprint = Blueprint("chatbot", __name__)
recognizer = sr.Recognizer()
engine = pyttsx3.init()

# Initialize Celery
celery = Celery(__name__, broker=current_app.config["REDIS_URL"])


# Function to get a temporary file path
def get_temp_file_path(suffix=".tmp"):
    return tempfile.NamedTemporaryFile(delete=False, suffix=suffix).name


# Celery task for transcription
@celery.task(name="transcribe_task")
def transcribe_task(audio_path, language):
    try:
        if language == "yoruba":
            transcript = transcribe_yoruba(audio_path)
        elif language == "fon":
            transcript = transcribe_fon(audio_path)
        else:
            transcript = transcribe_audio(audio_path, language=language)
        return transcript
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return "Could not transcribe audio"


# Image generation task
@celery.task(name="generate_image_task")
def generate_image_task(prompt):
    response = TextToImageGenerator.generate_image_from_text_stability(prompt=prompt)
    return response["image_url"]


# Image status route
@chatbot_blueprint.route("/image-status/<task_id>")
@jwt_required()
def image_status(task_id):
    task = generate_image_task.AsyncResult(task_id)
    if task.state == "SUCCESS":
        return jsonify({"status": task.state, "image_url": task.get()})
    else:
        return jsonify({"status": task.state})


@chatbot_blueprint.route("/chat", methods=["POST"])
@jwt_required()
def chat():
    try:
        user = User.query.get(get_jwt_identity())
        language = request.form.get("language", user.language_preference)

        audio_file = request.files.get("audio")
        text_input = request.form.get("text")
        image_url = request.form.get("image_url")  # Allow image URLs as input
        image_file = request.files.get("image")

        if (
            sum([bool(audio_file), bool(text_input), bool(image_url), bool(image_file)])
            > 1
        ):
            return (
                jsonify({"error": "Please provide only one type of input."}),
                400,
            )

        # --- Process Input (Text, Voice, or Image) ---
        translated_text = None  # Initialize translated_text
        image_tensor = None  # Initialize image_tensor
        inputs = None
        temp_file_path = None  # Store the path to the temporary file (image or audio)

        if audio_file:
            # --- Process Voice Input ---
            temp_file_path = get_temp_file_path(suffix=".wav")
            audio_file.save(temp_file_path)
            transcription_result = transcribe_task.delay(temp_file_path, language)
            transcript = transcription_result.get()

            if language != "English":
                translated_text = TranslationService.get_translation(
                    source_lang=language,
                    target_lang="English",
                    source_sentence=transcript,
                )
            else:
                translated_text = transcript

            # Prepare the input for LLaVA (text only for voice input)
            inputs = current_app.llava_processor(
                text=translated_text, return_tensors="pt"
            ).to(current_app.llava_model.device)

        elif text_input:
            # --- Process Text Input ---
            if language != "English":
                translated_text = TranslationService.get_translation(
                    source_lang=language,
                    target_lang="English",
                    source_sentence=text_input,
                )
            else:
                translated_text = text_input

            # Prepare the input for LLaVA (text only)
            inputs = current_app.llava_processor(
                text=translated_text, return_tensors="pt"
            ).to(current_app.llava_model.device)

        elif image_file or image_url:
            # --- Process Image Input ---
            if image_file:
                temp_file_path = get_temp_file_path(suffix=".jpg")
                image_file.save(temp_file_path)
                image = Image.open(temp_file_path)
            elif image_url:
                try:
                    response = requests.get(image_url, stream=True)
                    response.raise_for_status()
                    temp_file_path = get_temp_file_path(suffix=".jpg")
                    with open(temp_file_path, "wb") as f:
                        f.write(response.content)
                    image = Image.open(temp_file_path)
                except requests.exceptions.RequestException as e:
                    return jsonify({"error": f"Error downloading image: {e}"}), 500

            try:
                image_tensor = current_app.llava_processor(
                    images=image, return_tensors="pt"
                ).pixel_values.to(current_app.llava_model.device)
            except Exception as e:
                return (
                    jsonify({"error": f"Error processing image: {e}"}),
                    500,
                )

            # If there's associated text, combine with the image instruction
            if translated_text:
                text_input = translated_text + "\n<image>"
            else:
                text_input = "<image>"

            # Prepare the input for LLaVA (text and image)
            inputs = current_app.llava_processor(
                text=text_input, images=image_tensor, return_tensors="pt"
            ).to(current_app.llava_model.device)
        else:
            return (
                jsonify({"error": "Please provide text, audio, or image input."}),
                400,
            )

        # --- Generate Response using LLaVA ---
        try:
            generated_ids = current_app.llava_model.generate(
                **inputs, max_new_tokens=200
            )
            chatbot_response = current_app.llava_processor.batch_decode(
                generated_ids, skip_special_tokens=True
            )[0]
        except Exception as e:
            return jsonify({"error": f"Error generating response: {e}"}), 500

        # --- Sentiment Analysis ---
        analysis = TextBlob(chatbot_response)
        sentiment = analysis.sentiment.polarity
        current_app.logger.info(
            f"User Sentiment: {sentiment} (Text: {chatbot_response})"
        )

        # --- Dialogue Management ---
        states = [
            "greeting",
            "conversing",
            "confirming_image_generation",
            "generating_image",
            "confirming",
            "end",
        ]

        last_conversation = (
            Conversation.query.filter_by(user_id=user.id)
            .order_by(Conversation.timestamp.desc())
            .first()
        )

        current_state = "greeting"
        if last_conversation:
            current_state = last_conversation.dialogue_state

        # Dialogue Transitions and Responses
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
            # --- Check for image generation intent only if:
            #      - It's the first turn in the "conversing" state, OR
            #      - The previous turn was NOT an image input ---
            check_image_intent = (
                current_state == "conversing"
                and last_conversation.dialogue_state != "conversing"
            ) or (last_conversation and last_conversation.input_text != "<image>")
            if check_image_intent:
                # --- Use LLaVA to check for image generation intent ---
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

                # 1. Sentence Similarity Check
                response_embedding = current_app.sentence_embedding_model.encode(
                    translated_text, convert_to_tensor=True
                )
                image_generation_embeddings = (
                    current_app.sentence_embedding_model.encode(
                        image_generation_phrases, convert_to_tensor=True
                    )
                )
                cosine_scores = util.cos_sim(
                    response_embedding, image_generation_embeddings
                )
                max_similarity = cosine_scores.max().item()
                similarity_threshold = 0.7  # Adjust as needed

                if max_similarity >= similarity_threshold:
                    chatbot_response = "What would you like me to generate an image of?"
                    new_state = "confirming_image_generation"

                else:
                    # 2. Use LLaVA if sentence similarity is below the threshold
                    intent_prompt = f"The user said: '{translated_text}'."
                    " Does the user want to generate an image?"
                    intent_inputs = current_app.llava_processor(
                        text=intent_prompt, return_tensors="pt"
                    ).to(current_app.llava_model.device)
                    intent_generated_ids = current_app.llava_model.generate(
                        **intent_inputs, max_new_tokens=10
                    )
                    intent_response = current_app.llava_processor.batch_decode(
                        intent_generated_ids, skip_special_tokens=True
                    )[0]

                    if "yes" in intent_response.lower():
                        chatbot_response = (
                            "What would you like me to generate an image of?"
                        )
                        new_state = "confirming_image_generation"
                    else:
                        # --- Transition to Confirming (combined approach) ---
                        transition_to_confirming = False

                        # 1. Sentence Similarity Check
                        confirmation_phrases = [
                            "Is there anything else I can help you with?",
                            "Do you have any other questions?",
                            "Anything else I can assist you with today?",
                        ]
                        response_embedding = (
                            current_app.sentence_embedding_model.encode(
                                chatbot_response, convert_to_tensor=True
                            )
                        )
                        confirmation_embeddings = (
                            current_app.sentence_embedding_model.encode(
                                confirmation_phrases, convert_to_tensor=True
                            )
                        )
                        cosine_scores = util.cos_sim(
                            response_embedding, confirmation_embeddings
                        )
                        max_similarity = cosine_scores.max().item()
                        similarity_threshold = 0.8  # Adjust as needed
                        if max_similarity >= similarity_threshold:
                            transition_to_confirming = True

                        # 2. Turn-Taking Analysis
                        consecutive_short_responses = request.session.get(
                            "consecutive_short_responses", 0
                        )
                        short_response_threshold = 3  # Adjust as needed
                        short_response_length = 50  # Adjust as needed
                        if len(chatbot_response) <= short_response_length:
                            consecutive_short_responses += 1
                        else:
                            consecutive_short_responses = 0
                        request.session["consecutive_short_responses"] = (
                            consecutive_short_responses
                        )
                        if consecutive_short_responses >= short_response_threshold:
                            transition_to_confirming = True

                        if transition_to_confirming:
                            new_state = "confirming"
                        else:
                            new_state = "conversing"

            else:
                # --- Transition to Confirming (combined approach) ---
                transition_to_confirming = False

                # 1. Sentence Similarity Check
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
                cosine_scores = util.cos_sim(
                    response_embedding, confirmation_embeddings
                )
                max_similarity = cosine_scores.max().item()
                similarity_threshold = 0.8  # Adjust as needed
                if max_similarity >= similarity_threshold:
                    transition_to_confirming = True

                # 2. Turn-Taking Analysis
                consecutive_short_responses = request.session.get(
                    "consecutive_short_responses", 0
                )
                short_response_threshold = 3  # Adjust as needed
                short_response_length = 50  # Adjust as needed
                if len(chatbot_response) <= short_response_length:
                    consecutive_short_responses += 1
                else:
                    consecutive_short_responses = 0
                request.session["consecutive_short_responses"] = (
                    consecutive_short_responses
                )
                if consecutive_short_responses >= short_response_threshold:
                    transition_to_confirming = True

                if transition_to_confirming:
                    new_state = "confirming"
                else:
                    new_state = "conversing"

        elif current_state == "confirming_image_generation":
            if any(
                keyword in translated_text.lower()
                for keyword in ["yes", "sure", "okay", "yeah"]
            ):
                image_task = generate_image_task.delay(translated_text)
                chatbot_response = "Okay, I'm generating an image for you. "
                "You can check the status with the provided task ID."
                new_state = "generating_image"
            else:
                chatbot_response = (
                    "Alright, let's continue chatting then. What else is on your mind?"
                )
                new_state = "conversing"

        elif current_state == "generating_image":
            image_task_id = request.form.get(
                "image_task_id"
            )  # Get task ID from the request
            if not image_task_id:
                return jsonify({"error": "Missing image_task_id parameter."}), 400

            image_task = generate_image_task.AsyncResult(image_task_id)

            if image_task.state == "SUCCESS":
                image_url = image_task.get()
                chatbot_response = f"Here's the generated image: {image_url}"
                new_state = "confirming"
            elif image_task.state == "PENDING" or image_task.state == "STARTED":
                chatbot_response = (
                    "The image is still being generated. Please wait a bit."
                )
                new_state = "generating_image"  # Stay in the same state
            elif image_task.state == "FAILURE":
                chatbot_response = "Sorry, there was an error generating the image."
                " Please try again later."
                new_state = "conversing"  # Go back to conversing
            else:  # Unknown state
                chatbot_response = "I'm not sure what the status of the "
                "image generation is. Please try again later."
                new_state = "conversing"

        elif current_state == "confirming":
            if any(
                keyword in translated_text.lower()
                for keyword in ["yes", "sure", "please"]
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

        # --- End of Dialogue Management ---

        # Translate response back to the user's language
        if language != "English":
            translated_response = TranslationService.get_translation(
                source_lang="English",
                target_lang=language,
                source_sentence=chatbot_response,
            )
        else:
            translated_response = chatbot_response

        # Create a new Conversation record
        new_conversation = Conversation(
            user_id=user.id,
            input_text=translated_text if text_input or audio_file else "<image>",
            response_text=chatbot_response,
            input_language=language,
            output_language=user.language_preference,
            dialogue_state=new_state,
            image_path=temp_file_path if image_file or image_url else None,
        )
        current_app.db.session.add(new_conversation)
        current_app.db.session.commit()

        response_data = {"response": translated_response}

        if "image_task_id" in locals():
            response_data["image_task_id"] = image_task.id

        return jsonify(response_data)

    except redis.exceptions.RedisError as e:
        current_app.logger.error(f"Redis Error: {e}")
        return (
            jsonify({"error": "A database error occurred. Please try again later."}),
            500,
        )


# Schedule a task to delete old images
@celery.task(name="delete_old_images_task")
def delete_old_images_task():
    """Deletes image files associated with conversations older than a certain time."""
    try:
        image_expiry_time = datetime.utcnow() - timedelta(
            days=7
        )  # Set the desired expiry time (e.g., 7 days)

        old_conversations = Conversation.query.filter(
            # Filter conversations with image paths
            Conversation.image_path is not None,
            Conversation.timestamp < image_expiry_time,
        ).all()

        for conversation in old_conversations:
            if os.path.exists(conversation.image_path):
                os.remove(conversation.image_path)
                conversation.image_path = None  # Clear the path in the database
        current_app.db.session.commit()

        current_app.logger.info("Deleted old images successfully.")
    except Exception as e:
        current_app.logger.error(f"Error deleting old images: {e}")


# Schedule the cleanup task to run periodically (e.g., daily)
celery.conf.beat_schedule = {
    "delete_old_images": {
        "task": "delete_old_images_task",
        "schedule": crontab(minute=0, hour=0),  # Run daily at midnight
    }
}
