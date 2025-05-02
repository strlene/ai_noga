from pathlib import Path
from typing import Optional, Union, Iterable
import urllib.request

ROOT_DIR = Path(__file__).resolve().parents[1] / "uploads"
SEARCH_FOLDER = "composition"
DEFAULT_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff")

def _is_url(s: str) -> bool:
    return s.startswith(("http://", "https://"))

def _url_exists(url: str) -> bool:
    try:
        with urllib.request.urlopen(url) as resp:
            return resp.status == 200
    except Exception:
        return False
