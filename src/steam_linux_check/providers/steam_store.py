from dataclasses import asdict
from datetime import UTC, datetime, timedelta

import requests

from ..cache import is_cache_entry_fresh, load_json, save_json
from ..models import SteamStoreInfo

STEAM_APP_DETAILS_URL = "https://store.steampowered.com/api/appdetails"
CACHE_FILE = "steam_store.json"
CACHE_MAX_AGE = timedelta(days=7)

def get_app_details(app_id: int) -> SteamStoreInfo | None:
    """Fetch Steam Store metadata for one app."""

    cache = load_json(CACHE_FILE)
    cache_key = str(app_id)

    entry = cache.get(cache_key)

    if entry and is_cache_entry_fresh(entry, CACHE_MAX_AGE):
        return SteamStoreInfo(**entry["data"])

    response = requests.get(
        STEAM_APP_DETAILS_URL,
        params={"appids": app_id},
        timeout=15,
    )

    response.raise_for_status()

    result = response.json().get(cache_key)

    if not result or not result.get("success"):
        return None

    data = result["data"]
    platforms = data.get("platforms", {})

    info = SteamStoreInfo(
        app_id=app_id,
        name=data.get("name", "Unknown"),
        app_type=data.get("type", "unknown"),
        windows=platforms.get("windows", False),
        mac=platforms.get("mac", False),
        linux=platforms.get("linux", False),
    )

    cache[cache_key] = {
    "cached_at": datetime.now(UTC).isoformat(),
    "data": asdict(info),
}

    save_json(CACHE_FILE, cache)

    return info