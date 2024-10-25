import spacy
from app.models.Plant import Plant
from mongoengine import Q
from transformers import pipeline

nlp = spacy.load("en_core_web_lg")
classifier = pipeline("zero-shot-classification")


def enhance_response_with_plant_info(response_text):
    """
    Enhances a chatbot response with relevant plant information from the database.

    Args:
        response_text (str): Original response text

    Returns:
        str: Enhanced response text with additional plant information
    """
    # Extract plant names from the response
    doc = nlp(response_text)
    potential_plants = [ent.text for ent in doc.ents if ent.label_ == "ORG"]

    # Find relevant plants in the database
    found_plants = Plant.objects(Q(common_names__in=potential_plants))

    enhanced_response = response_text

    for plant in found_plants:
        # Prepare additional information
        additional_info = f"\n\nAdditional information about {plant.scientific_name}:\n"
        additional_info += f"- Common names: {', '.join(plant.common_names.get('en', []))}\n"

        # Add medicinal uses if available
        if plant.medicinal_uses:
            uses = plant.medicinal_uses.get("en", [])
            if uses:
                additional_info += f"- Traditional uses: {', '.join(uses)}\n"

        # Add chemical compounds if available
        if plant.chemical_compounds:
            compounds = [c["name"] for c in plant.chemical_compounds[:3]]
            if compounds:
                additional_info += f"- Key compounds: {', '.join(compounds)}\n"

        # Add conservation status if available
        if plant.conservation_status:
            additional_info += f"- Conservation status: {plant.conservation_status}\n"

        enhanced_response += additional_info

    return enhanced_response
