import json
from typing import Dict, Any, List, Optional

from function.validate_input_summary import extract_nama_list, validate_ingredients


# Dummy Gemini call (replace with actual working object)
# from your_module import _GEMINI



def validate_fix_typo_labels(data: Dict[str, Any]) -> Dict[str, Any]:
    ingredients = data.get("ingredients", [])
    ingredient_names = extract_nama_list(ingredients)

    print("ingredients:", ingredient_names)

    validated_ingredients = validate_ingredients(ingredient_names)

    print("validated_ingredients:", validated_ingredients)

    return {
        "validated_ingredients": validated_ingredients
    }
