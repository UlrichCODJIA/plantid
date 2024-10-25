import logging
import os
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime
from functools import wraps

import requests
from app.models import AuditLog
from flask import current_app, json
from flask_jwt_extended import create_access_token
from logger import configure_logger
from rdkit.Chem import Descriptors

logger = configure_logger(log_level=logging.DEBUG, log_file="logs/utils.log")


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
        raise ValueError("Input text cannot be empty or contain only whitespace characters.")

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


def store_backup(backup_data):
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"plantid_backup_{timestamp}.json"
    backup_path = os.path.join(current_app.config["BACKUP_STORAGE_PATH"], backup_filename)

    with open(backup_path, "w") as f:
        json.dump(backup_data, f)

    return backup_filename


def log_audit_event(user_id, action, details):
    audit_log = AuditLog(user_id=user_id, action=action, details=details)
    audit_log.save()


def calculate_molecular_descriptors(mol):
    """
    Calculates molecular descriptors for a given molecule.

    Args:
        mol: RDKit molecule object

    Returns:
        dict: Calculated descriptors
    """
    descriptors = {
        "mw": Descriptors.ExactMolWt(mol),
        "logp": Descriptors.MolLogP(mol),
        "hbd": Descriptors.NumHDonors(mol),
        "hba": Descriptors.NumHAcceptors(mol),
        "tpsa": Descriptors.TPSA(mol),
        "rotatable_bonds": Descriptors.NumRotatableBonds(mol),
    }
    return descriptors


def predict_molecular_targets(descriptors):
    """
    Predicts molecular targets based on calculated descriptors.
    This is a simplified version - in reality, you'd use a more sophisticated ML model.

    Args:
        descriptors (dict): Molecular descriptors

    Returns:
        list: Predicted targets with confidence scores
    """
    # This is a placeholder implementation
    potential_targets = [
        "Serotonin receptor",
        "Dopamine receptor",
        "Glucocorticoid receptor",
        "Cytochrome P450",
        "Cannabinoid receptor",
    ]

    predictions = []
    for target in potential_targets:
        # Simplified scoring based on molecular properties
        score = 0.0

        if 300 < descriptors["mw"] < 500:
            score += 0.2
        if 0 < descriptors["logp"] < 5:
            score += 0.2
        if descriptors["hbd"] < 5:
            score += 0.2
        if descriptors["hba"] < 10:
            score += 0.2
        if descriptors["tpsa"] < 140:
            score += 0.2

        if score > 0.5:
            predictions.append({"target": target, "confidence": round(score, 2)})

    return sorted(predictions, key=lambda x: x["confidence"], reverse=True)


def verify_written_consent(consent_info):
    """
    Verifies written consent.

    Args:
        consent_info (dict): Consent information

    Returns:
        bool: True if consent is verified, False otherwise
    """
    required_fields = ["provider_name", "signature", "date"]
    if not all(field in consent_info for field in required_fields):
        return False

    # TODO: Add additional verification logic
    return True


def verify_verbal_consent(consent_info):
    """
    Verifies verbal consent.

    Args:
        consent_info (dict): Consent information

    Returns:
        bool: True if consent is verified, False otherwise
    """
    required_fields = ["provider_name", "witness", "date"]
    if not all(field in consent_info for field in required_fields):
        return False

    # TODO: Add additional verification logic
    return True


def verify_community_consent(consent_info):
    """
    Verifies community consent.

    Args:
        consent_info (dict): Consent information

    Returns:
        bool: True if consent is verified, False otherwise
    """
    required_fields = ["community", "representative", "date"]
    if not all(field in consent_info for field in required_fields):
        return False

    # TODO: Add additional verification logic
    return True
