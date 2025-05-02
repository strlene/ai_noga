
from typing import Dict, Any, List
import google.generativeai as genai
import os
import json
import re
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
_GEMINI = genai.GenerativeModel("gemini-2.0-flash")

def extract_nama_list(ingredients: List[Dict[str, Any]]) -> List[str]:
    return [item["name"] for item in ingredients if "name" in item]

def extract_nama_list_nutrition_info(nutrition_info: List[Dict[str, Any]]) -> List[str]:
    return [item["nama"] for item in nutrition_info if "nama" in item]


def extract_json_from_response(text: str) -> str:
    # Remove markdown fencing like ```json or ```
    match = re.search(r"```(?:json)?\s*(\[\s*{.*?}\s*\])\s*```", text, re.DOTALL)
    if match:
        return match.group(1)
    return text.strip()



def extract_json_from_response_label(text: str) -> str:
    # Remove code block markers like ```json ... ```
    if "```" in text:
        text = text.replace("```json", "").replace("```", "").strip()
    try:
        start = text.index("[")
        end = text.rindex("]") + 1
        return text[start:end]
    except ValueError:
        print("JSON array not found in response.")
        return "[]"


def validate_ingredients(data: List[str]) -> List[Dict[str, Any]]:
    prompt = (
        "You are a food expert.\n"
        "Given a list of ingredient names, check for typos and correct them.\n"
        "Also indicate whether each is a valid ingredient.\n"
        "Return only a JSON array like:\n"
        "[{\"original\": \"suagr\", \"corrected\": \"sugar\", \"is_valid\": true}, ...]\n\n"
        f"List: {data}"
    )
    response = _GEMINI.generate_content(prompt)
    print("Gemini raw response:", response.text)

    raw = extract_json_from_response(response.text)
    try:
        return json.loads(raw)
    except Exception as e:
        print("JSON decode error (after cleaning):", str(e))
        return []

def validate_nutrition_info(data: List[str]) -> List[Dict[str, Any]]:
    if not data:
        print("Input list is empty.")
        return []

    prompt = (
        "You are a food expert.\n"
        "Given a list of nutrition attribute names (e.g., calories, sodium), check for typos and correct them.\n"
        "Also indicate whether each is a valid nutrition term.\n"
        "Return only a JSON array like:\n"
        "[{\"original\": \"calroies\", \"corrected\": \"calories\", \"is_nutrition\": true}, ...]\n\n"
        f"List: {data}"
    )

    try:
        response = _GEMINI.generate_content(prompt)
        raw = extract_json_from_response(response.text)

        return json.loads(raw)

    except Exception as e:
        print("Validation failed:", str(e))
        return []
