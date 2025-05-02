from typing import Dict, Optional, Any

from function.validate_input_summary import validate_ingredients, validate_nutrition_info


# Main function
def validate_fix_typo_labels(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        ingredients = data.get("ingredients", [])
        nutrition_info = data.get("nutrition_info", [])

        validated_ingredients = validate_ingredients(ingredients)
        validated_nutrition = validate_nutrition_info(nutrition_info)

        return {
            "validated_ingredients": validated_ingredients,
            "validated_nutrition_info": validated_nutrition
        }

    except Exception as e:
        print(f"Validation failed: {e}")
        return None