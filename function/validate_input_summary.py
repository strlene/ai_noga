
from typing import Dict, Any, List
import google.generativeai as genai
import os
import json

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
_GEMINI = genai.GenerativeModel("gemini-1.5-flash")


def validate_ingredients(data: List[str]) -> List[Dict[str, Any]]:
    prompt = (
        "You are a food expert.\n"
        "Given a list of ingredient names, check for typos and correct them.\n"
        "Also indicate whether each is a valid ingredient.\n"
        "Return only a JSON array like:\n"
        "[{'original': 'suagr', 'corrected': 'sugar', 'is_valid': true}, ...]\n\n"
        f"List: {data}"
    )
    response = _GEMINI.generate_content(prompt)
    return json.loads(response.text)

# Validate and classify nutrition info
def validate_nutrition_info(data: List[str]) -> List[Dict[str, Any]]:
    prompt = (
        "You are a nutrition expert.\n"
        "Given a list of terms, check for typos and correct them.\n"
        "Also classify whether each term refers to a nutrition attribute (e.g. calories, sodium).\n"
        "Return only a JSON array like:\n"
        "[{'original': 'calroies', 'corrected': 'calories', 'is_nutrition': true}, ...]\n\n"
        f"List: {data}"
    )
    response = _GEMINI.generate_content(prompt)
    return json.loads(response.text)
