from app.extensions import logger
from app.models import Plant
from app.utils.utils import calculate_molecular_descriptors, predict_molecular_targets
from rdkit import Chem, DataStructs
from rdkit.Chem import AllChem


def calculate_chemical_similarity(target_compound):
    """
    Calculates chemical similarity between a target compound and known compounds in the database.

    Args:
        target_compound (str): SMILES representation of the target compound

    Returns:
        list: Similar compounds with similarity scores
    """
    try:
        target_mol = Chem.MolFromSmiles(target_compound)
        if target_mol is None:
            return []

        target_fp = AllChem.GetMorganFingerprintAsBitVect(target_mol, 2)

        similar_compounds = []

        # Get all known compounds from plants in the database
        plants = Plant.objects
        for plant in plants:
            for compound in plant.chemical_compounds:
                try:
                    mol = Chem.MolFromSmiles(compound["smiles"])
                    if mol is not None:
                        fp = AllChem.GetMorganFingerprintAsBitVect(mol, 2)
                        similarity = DataStructs.TanimotoSimilarity(target_fp, fp)

                        if similarity >= 0.7:  # Threshold for similarity
                            similar_compounds.append(
                                {
                                    "name": compound["name"],
                                    "smiles": compound["smiles"],
                                    "similarity_score": round(similarity, 2),
                                    "plant": plant.scientific_name,
                                }
                            )
                except Exception as e:
                    logger.error(f"Error processing compound: {str(e)}")

        return sorted(similar_compounds, key=lambda x: x["similarity_score"], reverse=True)

    except Exception as e:
        logger.error(f"Error in chemical similarity calculation: {str(e)}")
        return []


def find_molecular_targets(compound_smiles):
    """
    Predicts potential molecular targets for a given compound using machine learning.

    Args:
        compound_smiles (str): SMILES representation of the compound

    Returns:
        list: Predicted molecular targets with confidence scores
    """
    try:
        mol = Chem.MolFromSmiles(compound_smiles)
        if mol is None:
            return []

        # Calculate molecular descriptors
        descriptors = calculate_molecular_descriptors(mol)

        # Use pre-trained model to predict targets
        predicted_targets = predict_molecular_targets(descriptors)

        return predicted_targets

    except Exception as e:
        logger.error(f"Error in molecular target prediction: {str(e)}")
        return []
