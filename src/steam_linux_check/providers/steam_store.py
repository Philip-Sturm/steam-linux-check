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
from ..errors import ProviderUnavailableError
from ..models import SteamStoreInfo

STEAM_APP_DETAILS_URL = "https://store.steampowered.com/api/appdetails"

CACHE_FILE = "steam_store.json"
CACHE_MAX_AGE = timedelta(days=7)

REQUEST_DELAY = 1.0
MAX_RETRIES = 4


def _load_stale_cache(
    cache: dict,
    cache_key: str,
) -> SteamStoreInfo | None:
    """Use an expired Steam Store cache entry as fallback."""

    data = get_cached_data(cache, cache_key)

    if data is None:
        return None

    print(
        "  Steam Store nicht erreichbar "
        "– alter Cache wird verwendet."
    )

    return SteamStoreInfo(**data)


def _raise_unavailable(
    app_id: int,
    message: str,
) -> None:
    """Raise a standardized provider availability error."""

    raise ProviderUnavailableError(
        provider="Steam Store",
        message=(
            f"Steam Store AppID {app_id}: "
            f"{message}"
        ),
    )


def get_app_details(app_id: int) -> SteamStoreInfo | None:
    """Fetch Steam Store metadata with cache and offline fallback."""

    cache = load_json(CACHE_FILE)
    cache_key = str(app_id)

    entry = cache.get(cache_key)

    # ---------------------------------------------------------
    # Frischer Cache
    # ---------------------------------------------------------

    if entry and is_cache_entry_fresh(entry, CACHE_MAX_AGE):
        if entry["data"] is None:
            return None

        return SteamStoreInfo(**entry["data"])

    # ---------------------------------------------------------
    # Netzwerkabfrage
    # ---------------------------------------------------------

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(
                STEAM_APP_DETAILS_URL,
                params={"appids": app_id},
                timeout=15,
            )

        except requests.RequestException:
            fallback = _load_stale_cache(
                cache,
                cache_key,
            )

            if fallback is not None:
                return fallback

            _raise_unavailable(
                app_id,
                "Netzwerkfehler und kein Cache vorhanden.",
            )

        # -----------------------------------------------------
        # Rate Limit
        # -----------------------------------------------------

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
                "  Steam Store Rate-Limit erreicht. "
                f"Warte {wait_time} Sekunden..."
            )

            time.sleep(wait_time)
            continue

        # -----------------------------------------------------
        # Temporärer Serverfehler
        # -----------------------------------------------------

        if 500 <= response.status_code < 600:
            wait_time = 5 * (attempt + 1)

            print(
                f"  Steam Store Serverfehler "
                f"{response.status_code}. "
                f"Neuer Versuch in {wait_time} Sekunden..."
            )

            time.sleep(wait_time)
            continue

        # -----------------------------------------------------
        # Andere HTTP-Fehler
        # -----------------------------------------------------

        try:
            response.raise_for_status()

        except requests.HTTPError:
            fallback = _load_stale_cache(
                cache,
                cache_key,
            )

            if fallback is not None:
                return fallback

            _raise_unavailable(
                app_id,
                f"HTTP-Fehler {response.status_code} "
                "und kein Cache vorhanden.",
            )

        # -----------------------------------------------------
        # JSON auswerten
        # -----------------------------------------------------

        try:
            response_data = response.json()

        except ValueError:
            fallback = _load_stale_cache(
                cache,
                cache_key,
            )

            if fallback is not None:
                return fallback

            _raise_unavailable(
                app_id,
                "ungültige Antwort und kein Cache vorhanden.",
            )

        if not isinstance(response_data, dict):
            fallback = _load_stale_cache(
                cache,
                cache_key,
            )

            if fallback is not None:
                return fallback

            _raise_unavailable(
                app_id,
                "unerwartetes Datenformat und kein Cache vorhanden.",
            )

        result = response_data.get(cache_key)

        # Keine Store-Daten für diese App
        if not result or not result.get("success"):
            cache[cache_key] = {
                "cached_at": datetime.now(UTC).isoformat(),
                "data": None,
            }

            save_json(CACHE_FILE, cache)

            time.sleep(REQUEST_DELAY)

            return None

        # -----------------------------------------------------
        # Erfolgreiche Antwort
        # -----------------------------------------------------

        data = result.get("data", {})
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

        time.sleep(REQUEST_DELAY)

        return info

    # ---------------------------------------------------------
    # Alle Versuche ausgeschöpft
    # ---------------------------------------------------------

    fallback = _load_stale_cache(
        cache,
        cache_key,
    )

    if fallback is not None:
        return fallback

    _raise_unavailable(
        app_id,
        "nach mehreren Versuchen keine Daten verfügbar.",
    )