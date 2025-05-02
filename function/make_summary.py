import ast
import json
import re
from typing import Dict, Any, Tuple, List

import genai
from fastapi import FastAPI

import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Inisialisasi model Gemini 1.5 Flash
_GEMINI = genai.GenerativeModel("gemini-1.5-flash")
app = FastAPI()

ALLERGEN_KEYWORDS = [
    "allergen", "allergenic", "may cause allergies", "may trigger allergies",
    "allergy", "hypersensitivity", "trigger reactions", "can cause reaction",
    "intolerance", "may affect allergic individuals"
]

def parse_value(nut: Dict[str, Any]) -> Tuple[float, str]:
    try:
        nilai = nut.get("nilai", 0)
        unit = nut.get("type", "").lower()
        return float(nilai), unit
    except (ValueError, TypeError):
        return 0.0, ""


def normalize_functions(raw: List[Dict[str, str]]) -> List[Dict[str, str]]:
    MAIN_ORDER = [
        "serving size", "calories", "total fat", "saturated fat", "total carbs", "sugar", "protein"
    ]
    aliases = {
        "serving size": "serving size",
        "takaran saji": "serving size",
        "calories": "calories",
        "kalori": "calories",
        "energy": "calories",
        "energi": "calories",
        "total fat": "total fat",
        "fat": "total fat",
        "lemak": "total fat",
        "saturated fat": "saturated fat",
        "lemak jenuh": "saturated fat",
        "total carbs": "total carbs",
        "carbohydrate": "total carbs",
        "karbohidrat": "total carbs",
        "karbo": "total carbs",
        "sugar": "sugar",
        "gula": "sugar",
        "protein": "protein",
    }
    normalized: Dict[str, Dict[str, str]] = {}
    for item in raw:
        name = item.get("nama", "").strip().lower()
        norm_name = aliases.get(name)
        if norm_name:
            normalized[norm_name] = {
                "nama": norm_name,
                "nilai": item.get("nilai", "0"),
                "type": item.get("type", ""),
            }
    for nutrient in MAIN_ORDER:
        if nutrient not in normalized:
            normalized[nutrient] = {
                "nama": nutrient,
                "nilai": "0",
                "type": "" if nutrient in {"serving size", "calories"} else "g"
            }

    return [normalized[n] for n in MAIN_ORDER] + [
        item for item in raw
        if aliases.get(item.get("nama", "").lower(), None) not in MAIN_ORDER
    ]


def make_summary(data: Dict[str, Any]) -> Dict[str, Any]:
    # count ingredient statuses and detect allergens
    good = neutral = bad = 0
    allergens: List[str] = []
    for ing in data.get("ingredients", []):
        s = ing.get("status", "")
        good += (s == "good")
        neutral += (s == "neutral")
        bad += (s == "bad")

        detail = ing.get("detail", "").lower()
        if any(keyword in detail for keyword in ALLERGEN_KEYWORDS):
            allergens.append(ing.get("nama", ""))

    # sugar & salt metrics
    high_sugar = mid_sugar = low_sugar = False
    high_salt = False
    sugar_amt = sugar_unit = None
    sodium_amt = sodium_unit = None
    for nut in data.get("nutrition_info", []):
        name = nut.get("nama", "").lower()
        num, unit = parse_value(nut)

        if name in ("sugar", "sugars"):
            sugar_amt, sugar_unit = num, unit
            if unit.startswith("gram"):
                if   num >= 22.5: high_sugar = True
                elif num > 5:     mid_sugar  = True
                else:             low_sugar  = True
        if name in ("sodium", "salt", "natrium"):
            sodium_amt, sodium_unit = num, unit
            if (unit == "mg" and num >= 2000) or (unit == "g" and num > 2):
                high_salt = True

    # vitamin detection
    vitamins = [ing.get("nama", "") for ing in data.get("ingredients", [])
                if ing.get("nama", "").lower().startswith("vitamin")]
    vitamins_rich = bool(vitamins)

    # AI: detect preservatives
    pres_prompt = f"""
You are an expert nutritionist. Given the product JSON below,
return a Python literal dict with key "preservatives_detected" listing any preservatives found.
Return ONLY the Python literal.

Product JSON:
{json.dumps(data)}
"""
    pres_resp = _GEMINI.generate_content(pres_prompt)
    try:
        pres_eval = ast.literal_eval(pres_resp.text)
        preservatives = [p.get("nama", "") for p in pres_eval.get("preservatives_detected", [])]
    except:
        preservatives = []

    top5 = [ing.get("nama", "") for ing in data.get("ingredients", [])[:5]]
    dairy_kw = {"milk","cheese","yogurt","cream","whey","casein","lactose"}
    dairy_count = sum(any(k in n.lower() for k in dairy_kw) for n in top5)
    dairy_based = dairy_count >= 2

    if high_sugar or high_salt or preservatives:
        overall = "Bad"
    elif neutral > good:
        overall = "Normal"
    else:
        overall = "Good"

    sugar_label = ("High Sugar" if high_sugar else
                   "Mid Sugar"  if mid_sugar  else
                   "Low Sugar"  if low_sugar  else
                   "Unknown")
    sodium_label = "High Sodium" if high_salt else "Normal Sodium"
    allergen_free = not allergens

    summary_statuses = {
        "Overall": overall,
        "Sugar Level": sugar_label,
        "Sodium Level": sodium_label,
        "Rich in Vitamins": "Yes" if vitamins_rich else "No",
        "Dairy-Based Product": "Yes" if dairy_based else "No",
        "Allergen-Free": "Yes" if allergen_free else "No",
        "Preservatives": "Yes" if preservatives else "No"
    }

    # AI: generate explanations
    explain_prompt = f"""
You are an expert nutritionist. For the given product JSON and its summary statuses below,
provide a brief explanation for each status, including why it was assigned and health implications.
Return ONLY a Python literal dict mapping each key to its explanation string.

Product JSON:
{json.dumps(data)}

Summary Statuses:
{json.dumps(summary_statuses)}
"""
    explain_resp = _GEMINI.generate_content(explain_prompt)
    resp_text = explain_resp.text
    # strip markdown fences if present
    if resp_text.startswith("```"):
        resp_text = re.sub(r"^```[a-zA-Z]*\n", "", resp_text)
        resp_text = re.sub(r"```$", "", resp_text)
    explanations = {}
    try:
        explanations = json.loads(resp_text)
    except:
        pass

    # build final summary with AI explanations
    summary_obj: Dict[str, Any] = {}
    for key, stat in summary_statuses.items():
        summary_obj[key] = {
            "status": stat,
            "description": explanations.get(key, "Explanation not available."),
        }

    return {"summary": [summary_obj], "preservatives_detected": preservatives,
            "nutrition_info": data.get("nutrition_info", []),
            "ingredients": data.get("ingredients", []),
            }


