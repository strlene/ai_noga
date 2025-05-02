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


