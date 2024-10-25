from datetime import datetime

from app.models import ConsentRecord
from app.utils.utils import verify_community_consent, verify_verbal_consent, verify_written_consent


def verify_consent(consent_info):
    """
    Verifies the consent provided for traditional knowledge submission.

    Args:
        user_id (int): The ID of the user submitting the knowledge
        consent_info (dict): Information about the consent
            {
                'provider_name': str,
                'community': str,
                'consent_type': str ('written', 'verbal', 'community'),
                'verification_method': str optional
            }

    Returns:
        bool: True if consent is verified, False otherwise
    """
    required_fields = ["provider_name", "consent_type"]
    if not all(field in consent_info for field in required_fields):
        return False

    if consent_info["consent_type"] == "written":
        return verify_written_consent(consent_info)
    elif consent_info["consent_type"] == "verbal":
        return verify_verbal_consent(consent_info)
    elif consent_info["consent_type"] == "community":
        return verify_community_consent(consent_info)

    return False


def record_consent(user_id, consent_info):
    """
    Records the consent information in the database.

    Args:
        user_id (int): The ID of the user submitting the knowledge
        consent_info (dict): Information about the consent

    Returns:
        dict: Recorded consent information
    """
    consent_record = ConsentRecord(
        user_id=user_id,
        consent_type=consent_info["consent_type"],
        provider_name=consent_info["provider_name"],
        community=consent_info.get("community"),
        verification_method=consent_info.get("verification_method"),
        verification_details=consent_info.get("verification_details"),
        terms=consent_info.get("terms", {}),
    )

    if "expiry_date" in consent_info:
        consent_record.expiry_date = datetime.strptime(consent_info["expiry_date"], "%Y-%m-%d")

    consent_record.save()

    return {
        "consent_id": consent_record.id,
        "consent_type": consent_record.consent_type,
        "provider_name": consent_record.provider_name,
        "consent_date": consent_record.consent_date.isoformat(),
    }
