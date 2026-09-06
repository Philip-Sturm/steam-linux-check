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
from ..models import ProtonDBInfo

PROTONDB_SUMMARY_URL = (
    "https://www.protondb.com/api/v1/reports/summaries/{app_id}.json"
)

CACHE_FILE = "protondb.json"
CACHE_MAX_AGE = timedelta(days=7)

REQUEST_DELAY = 1.0
MAX_RETRIES = 4


def _load_stale_cache(
    cache: dict,
    cache_key: str,
) -> ProtonDBInfo | None:
    """Use an expired cache entry as fallback."""

    data = get_cached_data(cache, cache_key)

    if data is None:
        return None

    print("  ProtonDB nicht erreichbar – alter Cache wird verwendet.")

    return ProtonDBInfo(**data)


def get_protondb_info(app_id: int) -> ProtonDBInfo | None:
    """Fetch ProtonDB data with cache and offline fallback."""

    cache = load_json(CACHE_FILE)
    cache_key = str(app_id)

    entry = cache.get(cache_key)

    # Frischer Cache
    if entry and is_cache_entry_fresh(entry, CACHE_MAX_AGE):
        if entry["data"] is None:
            return None

        return ProtonDBInfo(**entry["data"])

    # Netzwerkabfrage
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(
                PROTONDB_SUMMARY_URL.format(app_id=app_id),
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
                f"  ProtonDB AppID {app_id}: "
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
                "  ProtonDB Rate-Limit erreicht. "
                f"Warte {wait_time} Sekunden..."
            )

            time.sleep(wait_time)
            continue

        # Temporärer Serverfehler
        if 500 <= response.status_code < 600:
            wait_time = 5 * (attempt + 1)

            print(
                f"  ProtonDB Serverfehler "
                f"{response.status_code}. "
                f"Neuer Versuch in {wait_time} Sekunden..."
            )

            time.sleep(wait_time)
            continue

        # Keine ProtonDB-Daten vorhanden
        if response.status_code == 404:
            cache[cache_key] = {
                "cached_at": datetime.now(UTC).isoformat(),
                "data": None,
            }

            save_json(CACHE_FILE, cache)

            time.sleep(REQUEST_DELAY)

            return None

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
                f"  ProtonDB AppID {app_id}: "
                f"HTTP-Fehler {response.status_code} "
                "und kein Cache vorhanden."
            )

            return None

        # Erfolgreiche Antwort
        data = response.json()

        info = ProtonDBInfo(
            app_id=app_id,
            tier=data.get("tier"),
            confidence=data.get("confidence"),
            total_reports=data.get("total", 0),
            best_reported_tier=data.get("bestReportedTier"),
            trending_tier=data.get("trendingTier"),
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
        f"  ProtonDB AppID {app_id}: "
        "nach mehreren Versuchen keine Daten verfügbar."
    )

    return None