
import json
import re
from typing import List, Dict, Any

import mysql.connector
import mysql.connector
from fastapi import HTTPException

from function.ocr_utils import _extract_json, _GEMINI, OCRContentError, ocr_image
from model.table_health import GOOD, BAD, NEUTRAL


def _clean(text : str) -> str:
    text = re.sub(r"[^A-Za-zÀ-ÖØ-öø-ÿ\s]", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip().lower()

def _classify(name_clean: str) -> (str, str):
    if name_clean in GOOD:
        return "Good", GOOD[name_clean]
    if name_clean in BAD:
        return "Bad", BAD[name_clean]
    if name_clean in NEUTRAL:
        return "Neutral", NEUTRAL[name_clean]
    return "Neutral", "No clear consensus exists yet. Best consumed in moderation."


def normalize_ingredients(raw) -> List[Dict[str, str]]:
    if isinstance(raw, list) and raw and isinstance(raw[0], dict) and "name" in raw[0]:
        return raw

    if isinstance(raw, list):
        prompt = (
            "You are an expert nutritionist. Translate to English if necessary. "
            "Classify each ingredient as Good, Neutral, or Bad based on scientific studies. "
            "Return pure JSON array [{\"name\": \"...\", \"status\": \"good|neutral|bad\", \"detail\": \"...\"}]\n\n"
            + "\n".join(str(item) for item in raw)
        )
        resp = _GEMINI.generate_content(prompt, generation_config={"temperature": 0})
        return _extract_json(resp.text)

    return normalize_ingredients([raw])

def get_ingredients(source: str):
    try :
        raw = ocr_image(source, section="composition")
    except OCRContentError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not raw:
        raise HTTPException(status_code=400, detail="Ingredients not detected in image.")

    ingredients = normalize_ingredients(raw)
    return ingredients

def analyze_images(sessionId: str, sources: Dict[str, str]):
    data = {
        "ingredients": get_ingredients(sources["ingredients"]),
    }
    return {"status": "success", "data": data}

