import json
from typing import Dict, Any, List, Optional

from function.validate_input_summary import extract_nama_list, validate_ingredients, validate_nutrition_info, \
    extract_nama_list_nutrition_info


def validate_fix_typo_labels(data: Dict[str, Any]) -> Dict[str, Any]:
    ingredients = data.get("ingredients", [])
    ingredient_names = extract_nama_list(ingredients)
    validated_ingredients = validate_ingredients(ingredient_names)

    print("validated_ingredients:", validated_ingredients)

    return {
        "validated_ingredients": validated_ingredients
    }

def validate_fix_typo_nutrition_info_labels(data: Dict[str, Any]) -> Dict[str, Any]:
    nutrition_info = data.get("nutrition_info", [])
    nutrition_info_names = extract_nama_list_nutrition_info(nutrition_info)

    validated_nutrition_info = validate_nutrition_info(nutrition_info_names)

    print("validated_nutrition_info:", validated_nutrition_info)

    return {
        "validated_ingredients": validated_nutrition_info  # <-- this must match FastAPI schema
    }
