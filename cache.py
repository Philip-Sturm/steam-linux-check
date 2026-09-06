import json
from pathlib import Path

CACHE_DIR = Path("cache")


def load_json(filename: str) -> dict:
    path = CACHE_DIR / filename

    if not path.is_file():
        return {}

    return json.loads(path.read_text(encoding="utf-8"))


def save_json(filename: str, data: dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    path = CACHE_DIR / filename

    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )