import os
import urllib.request
import base64
import json
from pathlib import Path
from typing import List, Union, Dict, Any
from dotenv import load_dotenv
import google.generativeai as genai


load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
# _GEMINI = genai.GenerativeModel("gemini-1.5-flash")
_GEMINI = genai.GenerativeModel("gemini-2.0-flash")

def detect_food_from_image(image_source: Union[str, Path]) -> List[str]:
    if str(image_source).startswith(("http://", "https://")):
        with urllib.request.urlopen(str(image_source)) as resp:
            img_bytes = resp.read()
    else:
        with open(image_source, "rb") as f:
            img_bytes = f.read()

    img_b64 = base64.b64encode(img_bytes).decode()
    payload = [{
        "parts": [
            {"mime_type": "image/jpeg", "data": img_b64},
            {"text": (
                "Please identify all foods, beverages, drinks, or ingredients visible in this image. "
                "Only reply with a pure JSON array of strings, strictly like this: "
                "[\"white rice\", \"fried chicken\", \"chili sauce\", \"fried shallots\"]. "
                "No extra text or markdown."
            )}
        ]
    }]
    resp = _GEMINI.generate_content(payload, generation_config={"temperature": 0.0})
    raw = (resp.text or "").strip()
    if raw.startswith("```json"):
        raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        foods, _ = json.JSONDecoder().raw_decode(raw)
        if not isinstance(foods, list):
            raise ValueError(f"Expected list, got {type(foods)}")
        return foods
    except Exception as e:
        raise ValueError(f"Error parsing Gemini output: {e}\nRaw: {raw}")


def enrich_food_with_gemini(food_name: str) -> Dict[str, Any]:
    prompt = (
        "You are a professional nutritionist and food analyzer.\n"
        "Your task:\n"
        f"1. For the ingredient '{food_name}', research the most commonly used ingredients and their serving sizes.\n"
        "2. For each ingredient, output:\n"
        "   - name: the ingredient name\n"
        '   - status: one of "good", "neutral", or "bad"\n'
        "   - detail: one-sentence explanation (benefit if good, risk if bad, neutral note otherwise)\n"
        "3. Research the nutrition value of EACH ingredient: protein, carbohydrates, sugar, total fat, saturated fat, sodium.\n"
        "4. Sum all nutritional values and calculate the average calories per 100 g.\n"
        "5. Detect any preservatives.\n"
        "6. If the product is vitamin-rich, contains allergens, or is milk-based, note that in one sentence.\n"
        "Return ONLY this pure JSON object (no markdown, no extra text):\n"
        f'{{ "food_name": "{food_name}", "total_calories": "... kcal", '
        '"nutritional_info": [...], '
        '"ingredients": [ { "name": "...", "status": "...", "detail": "..." }, ... ], '
        '"summary": [...] }}'
    )
    resp = _GEMINI.generate_content({"parts": [{"text": prompt}]}, generation_config={"temperature": 0.2})
    raw = (resp.text or "").strip()
    if raw.startswith("```json"):
        raw = raw.replace("```json", "").replace("```", "").strip()
    idx = raw.find("{")
    if idx > 0:
        raw = raw[idx:]
    try:
        obj, _ = json.JSONDecoder().raw_decode(raw)
        return obj
    except json.JSONDecodeError as e:
        raise ValueError(f"Error parsing Gemini JSON for '{food_name}': {e}\nRaw: {raw}")

def enrich_summary_with_gemini(food_names: List[str]) -> str:
    prompt = (
        "You are a professional nutritionist.\n\n"
        f"Given these ingredients: {', '.join(food_names)}.\n"
        "Summarize in MAXIMUM 3 short sentences:\n"
        "- Main nutrients overall.\n"
        "- General health benefits.\n"
        "- Potential health risks.\n"
        "Return plain text only."
    )
    resp = _GEMINI.generate_content({"parts": [{"text": prompt}]}, generation_config={"temperature": 0.3})
    result = (resp.text or "").strip().replace("```", "").strip()
    return result


def enrich_summary_status_with_gemini(food_names: List[str]) -> str:
    prompt = (
        "You are a professional nutritionist.\n"
        "Classify each of the following ingredient names as one of: Good, Neutral, or Bad, based only on the name:\n"
        f"{', '.join(food_names)}\n"
        "Respond with a comma-separated list of labels in the same order, with no extra text or punctuation."
    )
    resp = _GEMINI.generate_content({"parts": [{"text": prompt}]}, generation_config={"temperature": 0.0})
    raw = (resp.text or "").strip()
    if raw.startswith("```") and raw.endswith("```"):
        raw = raw[3:-3].strip()
    raw = raw.replace("```", "").strip()
    if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
        raw = raw[1:-1].strip()
    labels = [lbl.strip().capitalize() for lbl in raw.split(",") if lbl.strip()]
    return labels[0] if labels else "Neutral"

DEFAULT_NUTRITION = [
    {"nama": "service size",   "status": "", "nilai": 0, "type": "gram"},
    {"nama": "calories",       "status": "", "nilai": 0, "type": "kilocalorie"},
    {"nama": "total fat",      "status": "", "nilai": 0, "type": "gram"},
    {"nama": "saturated fat",  "status": "", "nilai": 0, "type": "gram"},
    {"nama": "carbohydrates",  "status": "", "nilai": 0, "type": "gram"},
    {"nama": "sugar",          "status": "", "nilai": 0, "type": "gram"},
    {"nama": "protein",        "status": "", "nilai": 0, "type": "gram"},
]


def enrich_nutrition_info_with_gemini(dish_name: str) -> List[Dict[str, Any]]:
    prompt = (
        "You are a professional nutritionist.\n"
        f"Given the dish name: \"{dish_name}\", provide its overall nutritional information.\n"
        "Return ONLY a pure JSON array of objects, each with:\n"
        "  - \"nama\": nutrient name (e.g. \"Total Energy\", \"Sodium\")\n"
        "  - \"nilai\": numeric value (no units, just a number)\n"
        "  - \"type\": unit type (e.g. \"kilocalorie\", \"milligram\", \"gram\")\n"
        "If you have no data for this dish, return an empty array: []\n"
        "Example:\n"
        "[{\"nama\": \"Total Energy\", \"nilai\": 80, \"type\": \"kilocalorie\"}, "
        "{\"nama\": \"Sodium\", \"nilai\": 400, \"type\": \"milligram\"}]\n"
    )
    resp = _GEMINI.generate_content(
        {"parts": [{"text": prompt}]},
        generation_config={"temperature": 0.2}
    )
    raw = (resp.text or "").strip()
    # strip markdown fences if any
    raw = raw.replace("```json", "").replace("```", "").strip()
    # trim any leading text before '['
    idx = raw.find("[")
    raw = raw[idx:] if idx >= 0 else raw

    try:
        arr, _ = json.JSONDecoder().raw_decode(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Error parsing nutrition_info JSON: {e}\nRaw: {raw}")

    # if the model returned an empty list, use our defaults
    if not arr:
        # return a copy so we don't mutate DEFAULT_NUTRITION globally
        return [item.copy() for item in DEFAULT_NUTRITION]

    def classify(n: Dict[str, Any]) -> str:
        name = n.get("nama", "").lower()
        val = n.get("nilai", 0)
        unit = n.get("type", "").lower()
        if unit in ("kilocalorie", "kcal"):
            return "Bad" if val >= 2000 else "Neutral" if val >= 1000 else "Good"
        if "sodium" in name and unit in ("milligram", "mg"):
            return "Bad" if val >= 2000 else "Neutral" if val >= 500 else "Good"
        if "sugar" in name and unit in ("gram", "g"):
            return "Bad" if val >= 50 else "Neutral" if val >= 25 else "Good"
        if "protein" in name:
            return "Good"
        if unit in ("milligram", "gram") or "vitamin" in name or "mineral" in name:
            return "Good"
        return "Neutral"

    # classify each nutrient
    for nutrient in arr:
        nutrient["status"] = classify(nutrient)

    return arr

def handle_generate_healthy_recipe(payload: Dict[str, Any]) -> Dict[str, Any]:
    ingredients = payload.get("ingredients", [])
    nutrition_info = payload.get("nutrition_info", [])

    ingr_lines = "\n".join(f"{i['name']}: {i['status']}. {i['detail']}" for i in ingredients)
    nutri_lines = "\n".join(f"{n['nama']}: {n['nilai']} {n['type']}" for n in nutrition_info)

    prompt = (
        "You are a professional nutritionist and recipe developer.\n"
        "Given these ingredients:\n"
        f"{ingr_lines}\n"
        "And their nutritional values:\n"
        f"{nutri_lines}\n"
        "Propose a healthier recipe variation that includes:\n"
        "1. A new recipe name\n"
        "2. Ingredient substitutions with reasons\n"
        "3. Step-by-step cooking instructions\n"
        "Return ONLY a JSON object with keys:\n"
        "- \"recipe_name\": string\n"
        "- \"substitutions\": [{\"original\": string, \"substitute\": string, \"reason\": string}]\n"
        "- \"instructions\": [string]\n"
        "No extra text or markdown."
    )
    resp = _GEMINI.generate_content({"parts": [{"text": prompt}]}, generation_config={"temperature": 0.3})
    raw = (resp.text or "").strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Error parsing recipe JSON: {e}\nRaw: {raw}")



