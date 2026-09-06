import json
from datetime import UTC, datetime, timedelta
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


def is_cache_entry_fresh(entry: dict, max_age: timedelta) -> bool:
    """Return True if a cache entry is still within its lifetime."""

    cached_at = entry.get("cached_at")

    if not cached_at:
        return False

    try:
        timestamp = datetime.fromisoformat(cached_at)
    except ValueError:
        return False

    return datetime.now(UTC) - timestamp < max_age