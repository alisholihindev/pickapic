from pathlib import Path

import imagehash
from PIL import Image, UnidentifiedImageError


def compute_hashes(path: str) -> dict | None:
    """Return {phash, dhash, width, height} or None on error."""
    try:
        with Image.open(path) as img:
            img.load()
            w, h = img.size
            ph = str(imagehash.phash(img))
            dh = str(imagehash.dhash(img))
        return {"phash": ph, "dhash": dh, "width": w, "height": h}
    except (UnidentifiedImageError, OSError, Exception):
        return None


def hamming(a: str, b: str) -> int:
    ha = imagehash.hex_to_hash(a)
    hb = imagehash.hex_to_hash(b)
    return ha - hb
