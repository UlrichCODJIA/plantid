from flask_jwt_extended import create_access_token
from contextlib import contextmanager
import tempfile
import requests
import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)


def generate_microservice_token():
    try:
        return create_access_token(identity="chatbot_microservice")
    except Exception as e:
        raise Exception(f"Failed to generate microservice token: {e}") from e


@contextmanager
def temporary_jwt_secret_key(app, new_secret_key):
    original_secret_key = app.config["JWT_SECRET_KEY"]
    app.config["JWT_SECRET_KEY"] = new_secret_key
    try:
        yield
    finally:
        app.config["JWT_SECRET_KEY"] = original_secret_key


# Function to get a temporary file path
def get_temp_file_path(suffix=".tmp"):
    temp_dir = tempfile.gettempdir()
    temp_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False, dir=temp_dir)
    temp_file_path = temp_file.name
    temp_file.close()
    return temp_file_path


def retry_on_exception(retries=3, delay=5, exceptions=(Exception,)):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            while attempt < retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    logger.error(f"Error: {e}. Retrying in {delay} seconds...")
                    time.sleep(delay)
            logger.error(f"Failed after {retries} attempts.")
            return None

        return wrapper

    return decorator


def validate_text(text):
    """
    Validates the input text to ensure it meets the required criteria.

    Args:
        text (str): The input text to be validated.

    Returns:
        bool: True if the input text is valid, False otherwise.

    Raises:
        ValueError: If the input text is empty or contains only whitespace characters.
    """
    if not text or not text.strip():
        raise ValueError(
            "Input text cannot be empty or contain only whitespace characters."
        )

    return True


def handle_translation_error(error):
    """
    Handles translation errors and returns an appropriate error message.

    Args:
        error (Exception): The exception raised during translation.

    Returns:
        str: An error message describing the translation error.
    """
    if isinstance(error, ValueError):
        return f"Translation error: {str(error)}"
    else:
        return "An unexpected error occurred during translation."


def handle_image_generation_error(error):
    """
    Handles image generation errors and returns an appropriate error message.

    Args:
        error (Exception): The exception raised during image generation.

    Returns:
        str: An error message describing the image generation error.
    """
    if isinstance(error, ValueError):
        return f"Image generation error: {str(error)}"
    elif isinstance(error, requests.exceptions.RequestException):
        return f"API request error: {str(error)}"
    else:
        return "An unexpected error occurred during image generation."


def handle_text_to_speech_error(error):
    """
    Handles text-to-speech errors and returns an appropriate error message.

    Args:
        error (Exception): The exception raised during text-to-speech conversion.

    Returns:
        str: An error message describing the text-to-speech error.
    """
    if isinstance(error, ValueError):
        return f"Text-to-speech error: {str(error)}"
    elif isinstance(error, requests.exceptions.RequestException):
        return f"API request error: {str(error)}"
    else:
        return "An unexpected error occurred during text-to-speech conversion."
