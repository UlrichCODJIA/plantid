from flask import Blueprint, request, jsonify
import os
import speech_recognition as sr
import pyttsx3
import ollama

from utils.translation import TranslationService

speech_recognition_blueprint = Blueprint("speech_recognition", __name__)
recognizer = sr.Recognizer()
engine = pyttsx3.init()


@speech_recognition_blueprint.route("/voice-assistant", methods=["POST"])
def voice_assistant():
    language = request.form["language"]

    # Get audio from the request
    audio_file = request.files["audio"]
    audio_path = os.path.join("uploads", "audio.wav")
    audio_file.save(audio_path)

    # Transcribe audio to text
    with sr.AudioFile(audio_path) as source:
        audio = recognizer.record(source)
        text = recognizer.recognize_google(audio, language=language)

    # Translate text to English
    translated_text = TranslationService.get_translation(
        source_lang=language, target_lang="en", source_sentence=text
    )

    # Get chatbot response using Ollama API
    response = ollama.chat(
        model="mistral",
        messages=[
            {
                "role": "user",
                "content": translated_text,
            },
        ],
    )

    # Extract the chatbot's response from the API response
    chatbot_response = response["message"]["content"]

    # Translate response back to user's language
    translated_response = TranslationService.get_translation(
        source_lang="en", target_lang=language, source_sentence=chatbot_response
    )

    # Convert response to speech
    audio_response_path = os.path.join("uploads", "response.mp3")
    engine.save_to_file(translated_response, audio_response_path)
    engine.runAndWait()

    return jsonify({"response": translated_response, "audio_url": audio_response_path})
