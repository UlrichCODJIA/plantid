from app.models import FieldResearchData, Plant, ResearchPublication, db
from app.utils.chemical_similarity import calculate_chemical_similarity
from app.utils.molecular_target import find_molecular_targets
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

bp = Blueprint("research", __name__)


@bp.route("/publications/search", methods=["GET"])
@jwt_required()
def search_publications():
    query = request.args.get("query", "")
    plant_id = request.args.get("plant_id")
    compound = request.args.get("compound")

    publications = ResearchPublication.query

    if query:
        publications = publications.filter(
            (ResearchPublication.title.ilike(f"%{query}%")) | (ResearchPublication.abstract.ilike(f"%{query}%"))
        )

    if plant_id:
        publications = publications.join(ResearchPublication.plants).filter(Plant.id == plant_id)

    if compound:
        publications = publications.filter(ResearchPublication.chemical_compounds.contains([compound]))

    results = publications.all()
    return jsonify({"publications": [p.to_dict() for p in results]})


@bp.route("/chemical-similarity", methods=["POST"])
@jwt_required()
def find_similar_compounds():
    data = request.json
    if not data or "compound" not in data:
        return jsonify({"error": "No compound provided"}), 400

    target_compound = data["compound"]
    similar_compounds = calculate_chemical_similarity(target_compound)

    return jsonify({"similar_compounds": similar_compounds})


@bp.route("/molecular-targets", methods=["POST"])
@jwt_required()
def search_molecular_targets():
    data = request.json
    if not data or "compound" not in data:
        return jsonify({"error": "No compound provided"}), 400

    compound = data["compound"]
    targets = find_molecular_targets(compound)

    return jsonify({"molecular_targets": targets})


@bp.route("/field-data", methods=["POST"])
@jwt_required()
def submit_field_data():
    user_id = get_jwt_identity()
    data = request.json

    if not data or "plant_id" not in data:
        return jsonify({"error": "Incomplete field data"}), 400

    field_data = FieldResearchData(
        researcher_id=user_id,
        plant_id=data["plant_id"],
        location=data.get("location", {}),
        environmental_conditions=data.get("environmental_conditions", {}),
        samples_collected=data.get("samples_collected", {}),
        observations=data.get("observations", ""),
        images=data.get("images", []),
    )

    field_data.save()

    return jsonify({"message": "Field data submitted successfully", "field_data_id": field_data.id})
