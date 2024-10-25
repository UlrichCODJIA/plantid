from app.auth.user_auth import AuthResponseStatus, UserAuthenticator
from app.models import TraditionalKnowledge
from app.utils.consent import record_consent, verify_consent
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from plantid.app.chat.error_handling import handle_error

knowledge_blueprint = Blueprint("knowledge", __name__, url_prefix="/api/v1")


@knowledge_blueprint.route("/traditional-knowledge", methods=["POST"])
@jwt_required()
def submit_traditional_knowledge():
    user_id = get_jwt_identity()
    data = request.json

    if not data or "plant_id" not in data or "knowledge" not in data:
        return jsonify({"error": "Incomplete knowledge submission"}), 400

    consent_verified = verify_consent(data.get("consent_info", {}))
    if not consent_verified:
        return jsonify({"error": "Consent verification failed"}), 403

    consent_record = record_consent(user_id, data.get("consent_info", {}))

    knowledge = TraditionalKnowledge(
        plant_id=data["plant_id"],
        contributor_id=user_id,
        knowledge_text=data["knowledge"],
        source_region=data.get("region", ""),
        consent_record=consent_record,
    )

    knowledge.save()

    return jsonify({"message": "Traditional knowledge submitted successfully", "knowledge_id": knowledge.id})


@knowledge_blueprint.route("/traditional-knowledge/<int:knowledge_id>/verify", methods=["POST"])
@jwt_required()
def verify_knowledge(knowledge_id):
    user_id = get_jwt_identity()
    authenticator = UserAuthenticator()
    response = authenticator.authenticate_user(user_id)
    if not response.status == AuthResponseStatus.SUCCESS:
        return handle_error("Unauthorized access", 403)
    user = response.user

    if not user.is_verified_researcher:
        return jsonify({"error": "Unauthorized"}), 403

    knowledge = TraditionalKnowledge.objects.get_or_404(_id=knowledge_id)
    knowledge.verification_status = "verified"
    knowledge.save()

    return jsonify({"message": "Knowledge verified successfully"})
