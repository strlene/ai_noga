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
def get_image_path_non_labels(
    basename: str,
    root: Union[str, Path] = ROOT_DIR,
    *,
    extensions: Iterable[str] = DEFAULT_EXTENSIONS,
    strict_ext: bool = False,
) -> Optional[Union[Path, str]]:
    """
    - Jika URL absolut → cek apakah reachable → return URL (string).
    - Jika nama file lokal → cari file di uploads/composition.
    """

    if _is_url(basename):
        return basename if _url_exists(basename) else None

    root = Path(root)
    search_dir = root / SEARCH_FOLDER
    supplied_path = search_dir / basename

    if supplied_path.is_file():
        return supplied_path

    name = Path(basename).stem
    candidate_names = []
    if strict_ext:
        candidate_names.append(basename)
    else:
        candidate_names.extend(f"{name}{ext}" for ext in extensions)

    for candidate in candidate_names:
        candidate_path = search_dir / candidate
        if candidate_path.is_file():
            return candidate_path

    return None

