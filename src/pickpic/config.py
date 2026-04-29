from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path

APP_NAME = "Pickapic"
APP_REPO_URL = "https://github.com/alisholihindev/pickapic"
APP_RELEASES_URL = f"{APP_REPO_URL}/releases"
APP_SUPPORT_URL = "https://ko-fi.com/alisholihin"
APP_DIR = Path.home() / ".pickpic"
ASSETS_DIR = Path(__file__).resolve().parent / "assets"
APP_LOGO_PATH = ASSETS_DIR / "pickapic-logo.png"
APP_ICON_PATH = ASSETS_DIR / "pickapic-icon.ico"
DB_PATH = APP_DIR / "index.db"
THUMB_CACHE_DIR = APP_DIR / "thumbs"
SETTINGS_PATH = APP_DIR / "settings.json"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff", ".tif", ".raw", ".cr2", ".nef"}

HASH_DISTANCE_EXACT = 0
THUMB_SIZE = (160, 160)
SCAN_CHUNK = 1000
RESULTS_PAGE = 50

PRESETS: dict[str, dict] = {
    "strict":  {"hash_distance_similar": 5,  "blur_threshold": 50.0,  "min_file_size_kb": 0},
    "normal":  {"hash_distance_similar": 10, "blur_threshold": 100.0, "min_file_size_kb": 0},
    "loose":   {"hash_distance_similar": 20, "blur_threshold": 200.0, "min_file_size_kb": 0},
}


@dataclass
class Settings:
    hash_distance_similar: int = 10
    blur_threshold: float = 100.0
    min_file_size_kb: int = 0
    image_display_orientation: str = "landscape"
    feature_duplicates: bool = True
    feature_blur: bool = True
    feature_gps: bool = True

    @classmethod
    def load(cls) -> "Settings":
        if SETTINGS_PATH.exists():
            try:
                data = json.loads(SETTINGS_PATH.read_text())
                known = set(cls.__dataclass_fields__)
                return cls(**{k: v for k, v in data.items() if k in known})
            except Exception:
                pass
        return cls()

    def save(self) -> None:
        APP_DIR.mkdir(parents=True, exist_ok=True)
        SETTINGS_PATH.write_text(json.dumps(asdict(self), indent=2))

    def apply_preset(self, name: str) -> None:
        p = PRESETS[name]
        self.hash_distance_similar = p["hash_distance_similar"]
        self.blur_threshold = p["blur_threshold"]
        self.min_file_size_kb = p["min_file_size_kb"]

    @property
    def active_preset(self) -> str | None:
        for name, vals in PRESETS.items():
            if (
                self.hash_distance_similar == vals["hash_distance_similar"]
                and self.blur_threshold == vals["blur_threshold"]
                and self.min_file_size_kb == vals["min_file_size_kb"]
            ):
                return name
        return None
