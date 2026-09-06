import time
from dataclasses import asdict
from datetime import UTC, datetime, timedelta

import requests

from ..cache import (
    get_cached_data,
    is_cache_entry_fresh,
    load_json,
    save_json,
)
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


def _load_stale_cache(
    cache: dict,
    cache_key: str,
) -> SteamDeckInfo | None:
    """Use an expired Steam Deck cache entry as fallback."""

    data = get_cached_data(cache, cache_key)

    if data is None:
        return None

    print(
        "  Steam Deck / SteamOS nicht erreichbar "
        "– alter Cache wird verwendet."
    )

    return SteamDeckInfo(**data)


def get_steam_deck_info(app_id: int) -> SteamDeckInfo | None:
    """Fetch Steam Deck data with cache and offline fallback."""

    cache = load_json(CACHE_FILE)
    cache_key = str(app_id)

    entry = cache.get(cache_key)

    # Frischer Cache
    if entry and is_cache_entry_fresh(entry, CACHE_MAX_AGE):
        if entry["data"] is None:
            return None

        return SteamDeckInfo(**entry["data"])

    # Netzwerkabfrage
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(
                STEAM_DECK_URL,
                params={"nAppID": app_id},
                timeout=15,
            )

        except requests.RequestException:
            fallback = _load_stale_cache(
                cache,
                cache_key,
            )

            if fallback is not None:
                return fallback

            print(
                f"  Steam Deck AppID {app_id}: "
                "Netzwerkfehler und kein Cache vorhanden."
            )

            return None

        # Rate Limit
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")

            if retry_after is not None:
                try:
                    wait_time = int(retry_after)
                except ValueError:
                    wait_time = 30 * (attempt + 1)
            else:
                wait_time = 30 * (attempt + 1)

            print(
                "  Steam-Deck Rate-Limit erreicht. "
                f"Warte {wait_time} Sekunden..."
            )

            time.sleep(wait_time)
            continue

        # Serverfehler
        if 500 <= response.status_code < 600:
            wait_time = 5 * (attempt + 1)

            print(
                f"  Steam-Deck Serverfehler "
                f"{response.status_code}. "
                f"Neuer Versuch in {wait_time} Sekunden..."
            )

            time.sleep(wait_time)
            continue

        # Andere HTTP-Fehler
        try:
            response.raise_for_status()

        except requests.HTTPError:
            fallback = _load_stale_cache(
                cache,
                cache_key,
            )

            if fallback is not None:
                return fallback

            print(
                f"  Steam Deck AppID {app_id}: "
                f"HTTP-Fehler {response.status_code} "
                "und kein Cache vorhanden."
            )

            return None

        # JSON lesen
        try:
            data = response.json()

        except ValueError:
            fallback = _load_stale_cache(
                cache,
                cache_key,
            )

            if fallback is not None:
                return fallback

            print(
                f"  Steam Deck AppID {app_id}: "
                "ungültige Antwort und kein Cache vorhanden."
            )

            return None

        # Keine verwertbaren Daten
        if not data.get("success"):
            cache[cache_key] = {
                "cached_at": datetime.now(UTC).isoformat(),
                "data": None,
            }

            save_json(CACHE_FILE, cache)

            time.sleep(REQUEST_DELAY)

            return None

        results = data.get("results")

        if not isinstance(results, dict):
            cache[cache_key] = {
                "cached_at": datetime.now(UTC).isoformat(),
                "data": None,
            }

            save_json(CACHE_FILE, cache)

            time.sleep(REQUEST_DELAY)

            return None

        # Erfolgreiche Antwort
        info = SteamDeckInfo(
            app_id=app_id,
            deck_category=results.get("resolved_category"),
            steamos_category=results.get(
                "steamos_resolved_category"
            ),
        )

        cache[cache_key] = {
            "cached_at": datetime.now(UTC).isoformat(),
            "data": asdict(info),
        }

        save_json(CACHE_FILE, cache)

        time.sleep(REQUEST_DELAY)

        return info

    # Alle Versuche ausgeschöpft
    fallback = _load_stale_cache(
        cache,
        cache_key,
    )

    if fallback is not None:
        return fallback

    print(
        f"  Steam Deck AppID {app_id}: "
        "nach mehreren Versuchen keine Daten verfügbar."
    )

    return None