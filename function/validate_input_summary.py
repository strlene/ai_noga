
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

def extract_json_from_response(text: str) -> str:
    # Remove markdown fencing like ```json or ```
    match = re.search(r"```(?:json)?\s*(\[\s*{.*?}\s*\])\s*```", text, re.DOTALL)
    if match:
        return match.group(1)
    return text.strip()

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
