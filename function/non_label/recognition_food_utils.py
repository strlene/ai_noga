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
