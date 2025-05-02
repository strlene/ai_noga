from __future__ import annotations

import base64, json, os, re, urllib.request
from pathlib import Path
from typing import Iterable, Optional

from dotenv import load_dotenv
import google.generativeai as genai


class OCRContentError(Exception):
    pass

ROOT_DIR = Path(__file__).resolve().parents[1] / "uploads"
SEARCH_ORDER: Iterable[str] = ("composition")
DEFAULT_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff")

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
_GEMINI = genai.GenerativeModel("gemini-2.0-flash")

_PROMPTS = {
    "composition": (
        "Extract the list of ingredients from this product label. "
        "For EACH ingredient, classify the status as "
        "\"good\", \"neutral\", or \"bad\" based on these criteria:\n"
        "• good  = safe to consume regularly in large amounts; beneficial\n"
        "• neutral = potentially harmful if consumed excessively; scientific evidence is inconclusive\n"
        "• bad  = strong evidence of harm with regular consumption\n\n"
        "Return **ONLY** a pure JSON array in the format:\n"
        "[{\"nama\":\"...\",\"status\":\"good|neutral|bad\",\"detail\":\"...\"}, ...]\n"
        "All output in **English**, no markdown, no extra explanation."
    ),

}