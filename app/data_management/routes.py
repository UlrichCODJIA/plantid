import pandas as pd
from app.auth.user_auth import AuthResponseStatus, UserAuthenticator
from app.chat.error_handling import handle_error
from app.models.AuditLog import AuditLog
from app.models.Plant import Plant
from app.models.ResearchPublication import ResearchPublication
from app.models.TraditionalKnowledge import TraditionalKnowledge

# from app.utils.utils import store_backup
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

data_management_blueprint = Blueprint("data_management", __name__)


@data_management_blueprint.route("/export", methods=["GET"])
@jwt_required()
def export_data():
    data_type = request.args.get("type", "all")
    format = request.args.get("format", "json")

    if data_type == "plants":
        data = Plant.objects
        exported_data = [plant.to_dict() for plant in data]
    elif data_type == "knowledge":
        data = TraditionalKnowledge.objects
        exported_data = [knowledge.to_dict() for knowledge in data]
    elif data_type == "publications":
        data = ResearchPublication.objects
        exported_data = [pub.to_dict() for pub in data]
    else:
        plants = [plant.to_dict() for plant in Plant.objects]
        knowledge = [k.to_dict() for k in TraditionalKnowledge.objects]
        publications = [pub.to_dict() for pub in ResearchPublication.objects]

        exported_data = {"plants": plants, "traditional_knowledge": knowledge, "publications": publications}

    if format == "csv":
        if isinstance(exported_data, list):
            df = pd.DataFrame(exported_data)
        else:
            df = pd.concat([pd.DataFrame(v) for k, v in exported_data.items()], keys=exported_data.keys())
        return df.to_csv()
    else:
        return jsonify(exported_data)


# @data_management_blueprint.route("/backup", methods=["POST"])
# @jwt_required()
# def create_backup():
#     user_id = get_jwt_identity()
#     authenticator = UserAuthenticator()
#     response = authenticator.authenticate_user(user_id)
#     if not response.status == AuthResponseStatus.SUCCESS:
#         return handle_error("Unauthorized access", 403)
#     user = response.user

#     if not user.role == "admin":
#         return jsonify({"error": "Unauthorized"}), 403

#     # Create backup of all data
#     backup_data = {
#         "plants": [plant.to_dict() for plant in Plant.objects],
#         "traditional_knowledge": [k.to_dict() for k in TraditionalKnowledge.objects],
#         "publications": [pub.to_dict() for pub in ResearchPublication.objects],
#         "users": [user.to_dict() for user in User.objects],
#     }

#     backup_id = store_backup(backup_data)

#     return jsonify({"message": "Backup created successfully", "backup_id": backup_id})


@data_management_blueprint.route("/audit-log", methods=["GET"])
@jwt_required()
def get_audit_log():
    user_id = get_jwt_identity()
    authenticator = UserAuthenticator()
    response = authenticator.authenticate_user(user_id)
    if not response.status == AuthResponseStatus.SUCCESS:
        return handle_error("Unauthorized access", 403)
    user = response.user

    if not user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403

    audit_logs = AuditLog.objects().order_by("timestamp")[:101]

    return jsonify({"audit_logs": [log.to_dict() for log in audit_logs]})
