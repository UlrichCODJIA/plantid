import re
import requests

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
        raise ValueError("Input text cannot be empty or contain only whitespace characters.")

    # Add any additional validation rules as needed
    # For example, check if the text contains only alphanumeric characters:
    # if not re.match(r'^[\w\s]+$', text):
    #     raise ValueError("Input text must contain only alphanumeric characters and whitespace.")

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