from __future__ import annotations

import base64, json, os, re, urllib.request
from pathlib import Path
from typing import Iterable, Optional

from dotenv import load_dotenv
import google.generativeai as genai


class OCRContentError(Exception):
    pass

ROOT_DIR = Path(__file__).resolve().parents[1] / "uploads"
SEARCH_ORDER: Iterable[str] = ("nutrition_info")
DEFAULT_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff")

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
_GEMINI = genai.GenerativeModel("gemini-2.0-flash")

_PROMPTS = {
    "nutrition_info": (
        "Extract the nutrition facts table from this image. "
        "For each nutrition fact, return a JSON object with the following fields: "
        "{\"nama\": \"...\", \"nilai\": ..., \"type\": \"...\", \"input\": null, "
        "\"data\": {\"nama\": \"...\", \"nilai\": ..., \"input\": null}, "
        "\"status\": \"good|neutral|bad\", \"detail\": \"...\"}. "
        "Classify each nutrient as Good, Neutral, or Bad based on its health impact (e.g. sugar and saturated fat are Bad in excess; vitamins and minerals are Good). "
        "'nilai' must be a pure number (integer or float), without any units or symbols. "
        "'type' must translate the original unit into a word, as follows: "
        "'%' → 'percent', 'g' → 'gram', 'mg' → 'milligram', 'mcg' → 'microgram', 'kcal' or 'kkal' → 'kilocalorie'. "
        "If no unit is detected, set 'type' to 'none'. "
        "The 'data' field must repeat the cleaned 'nama', 'nilai' (as number), and 'input'. "
        "Translate to English if necessary. Reply ONLY with a pure JSON array. Do not add any explanations, extra text, or markdown."
    ),
}

def _is_url(s: str) -> bool:
    return s.startswith(("http://", "https://"))

def _download_url(url: str) -> bytes:
    with urllib.request.urlopen(url) as resp:
        if resp.status != 200:
            raise FileNotFoundError(f"URL tidak dapat diakses: {url}")
        return resp.read()

def _resolve_local(basename: str) -> Path:
    root = ROOT_DIR
    stem = Path(basename).stem
    supplied_ext = Path(basename).suffix.lower()

    cand: list[str] = (
        [f"{stem}{supplied_ext}", *(
            f"{stem}{ext}" for ext in DEFAULT_EXTENSIONS if ext != supplied_ext
        )] if supplied_ext else
        [f"{stem}{ext}" for ext in DEFAULT_EXTENSIONS]
    )

    for sub in SEARCH_ORDER:
        for c in cand:
            p = root / sub / c
            if p.is_file():
                return p
    raise FileNotFoundError(f"File lokal tidak ditemukan: {basename}")

def _img_bytes(src: str) -> bytes:
    if _is_url(src):
        return _download_url(src)
    p = Path(src)
    return p.read_bytes() if p.is_file() else _resolve_local(src).read_bytes()

def _guess_section(src: str) -> str:
    return next((s for s in SEARCH_ORDER if s in src), "composition")

_JSON_RE = re.compile(r"(\{[\s\S]*?\}|\[[\s\S]*?\])", re.S)

def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        nl = text.find("\n")
        if nl != -1:
            text = text[nl + 1 :]
    if text.endswith("```"):
        text = text[:-3].rstrip()
    return text.strip()

def _extract_json(raw: str):
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        cleaned = _strip_fences(raw)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            match = _JSON_RE.search(cleaned)
            if match:
                return json.loads(match.group(1))
        raise OCRContentError("Gambar tidak mengandung data ingredients atau nutrition info yang valid.")

def ocr_image(
    source: str,
    *,
    section: Optional[str] = None,
    temperature: float = 0.0,
):
    section = section or _guess_section(source)
    if section not in _PROMPTS:
        raise ValueError(f"Section tak dikenal: {section!r}")

    img_bytes = _img_bytes(source)
    mime_type = "image/jpeg" if source.lower().endswith((".jpg", ".jpeg")) else "image/png"
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")

    contents = [{
        "parts": [
            {"mime_type": mime_type, "data": img_b64},
            {"text": _PROMPTS[section]},
        ]
    }]
    resp = _GEMINI.generate_content(contents, generation_config={"temperature": temperature})
    return _extract_json(resp.text)
