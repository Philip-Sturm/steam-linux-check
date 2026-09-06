import time
from dataclasses import asdict
from datetime import UTC, datetime, timedelta

import requests

from ..cache import is_cache_entry_fresh, load_json, save_json
from ..models import SteamDeckInfo


STEAM_DECK_URL = (
    "https://store.steampowered.com/"
    "saleaction/ajaxgetdeckappcompatibilityreport"
)

CACHE_FILE = "steam_deck.json"
CACHE_MAX_AGE = timedelta(days=7)

REQUEST_DELAY = 1.0
MAX_RETRIES = 4


DECK_CATEGORIES = {
    1: "Unsupported",
    2: "Playable",
    3: "Verified",
}


def category_name(category: int | None) -> str:
    """Convert Steam compatibility category to a readable name."""

    if category is None:
        return "Unknown"

    return DECK_CATEGORIES.get(category, "Unknown")


def get_steam_deck_info(app_id: int) -> SteamDeckInfo | None:
    """Fetch Steam Deck and SteamOS compatibility information."""

    cache = load_json(CACHE_FILE)
    cache_key = str(app_id)

    entry = cache.get(cache_key)

    if entry and is_cache_entry_fresh(entry, CACHE_MAX_AGE):
        if entry["data"] is None:
            return None

        return SteamDeckInfo(**entry["data"])

    for attempt in range(MAX_RETRIES):
        response = requests.get(
            STEAM_DECK_URL,
            params={"nAppID": app_id},
            timeout=15,
        )

        if response.status_code == 429:
            wait_time = 30 * (attempt + 1)

            print(
                f"  Steam-Deck Rate-Limit erreicht. "
                f"Warte {wait_time} Sekunden..."
            )

            time.sleep(wait_time)
            continue

        response.raise_for_status()

        data = response.json()

        if not data.get("success"):
            cache[cache_key] = {
                "cached_at": datetime.now(UTC).isoformat(),
                "data": None,
            }

            save_json(CACHE_FILE, cache)

            time.sleep(REQUEST_DELAY)
            return None

        results = data.get("results", {})

        info = SteamDeckInfo(
            app_id=app_id,
            deck_category=results.get("resolved_category"),
            steamos_category=results.get("steamos_resolved_category"),
        )

        cache[cache_key] = {
            "cached_at": datetime.now(UTC).isoformat(),
            "data": asdict(info),
        }

        save_json(CACHE_FILE, cache)

        time.sleep(REQUEST_DELAY)

        return info

    print(
        f"  Steam-Deck AppID {app_id}: "
        "nach mehreren Versuchen übersprungen."
    )

    return None