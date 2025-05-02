
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




def get_nutrition_info(source: str):
    try:
        raw = ocr_image(source, section="nutrition_info")
    except OCRContentError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not raw:
        raise HTTPException(status_code=400, detail="Nutrition info not detected in image.")

    return map_nutrition_info(raw)


def map_nutrition_info(raw_nutrition_info: Any) -> List[Dict[str, Any]]:
    mapped: List[Dict[str, Any]] = []

    for item in raw_nutrition_info:
        # Ambil nama, nilai, type
        if isinstance(item, dict) and "nama" in item and "nilai" in item:
            nama = item["nama"]
            nilai = item["nilai"]
            type_ = item.get("type")
            status = item.get("status")
        elif isinstance(item, dict) and len(item) == 1:
            nama, nilai = next(iter(item.items()))
            type_ = None
            status = None
        else:
            nama = None
            nilai = 0
            type_ = None
            status = None


        mapped.append({
            "nama": nama,
            "nilai": nilai,
            "type": type_,
            "status": status,
        })

    return mapped


def analyze_images(sessionId: str, sources: Dict[str, str]):
    data = {
        "nutrition_info": get_nutrition_info(sources["nutrition_info"])
    }
    return {"status": "success", "data": data}

