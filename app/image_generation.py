from flask import Blueprint, request, jsonify

from utils.text_to_image import TextToImageGenerator
from utils.translation import TranslationService

image_generation_blueprint = Blueprint("image_generation", __name__)


@image_generation_blueprint.route("/generate", methods=["POST"])
def generate_image():
    text = request.form["text"]
    language = request.form["language"]

    # Translate text to English
    translated_text = TranslationService.get_translation(
        source_lang=language, target_lang="en", source_sentence=text
    )

    # Generate image from text using Ollama API
    response = TextToImageGenerator.generate_image_from_text_stability(
        prompt=translated_text
    )
    generated_image_url = response["image_url"]

    return jsonify({"image_url": generated_image_url})
