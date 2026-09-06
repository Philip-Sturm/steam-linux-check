import time
from dataclasses import asdict
from datetime import UTC, datetime, timedelta

import requests

from ..cache import is_cache_entry_fresh, load_json, save_json
from ..models import ProtonDBInfo


PROTONDB_SUMMARY_URL = (
    "https://www.protondb.com/api/v1/reports/summaries/{app_id}.json"
)

CACHE_FILE = "protondb.json"
CACHE_MAX_AGE = timedelta(days=7)

REQUEST_DELAY = 1.0
MAX_RETRIES = 4


def get_protondb_info(app_id: int) -> ProtonDBInfo | None:
    """Fetch ProtonDB summary information for one Steam app."""

    cache = load_json(CACHE_FILE)
    cache_key = str(app_id)

    entry = cache.get(cache_key)

    if entry and is_cache_entry_fresh(entry, CACHE_MAX_AGE):
        if entry["data"] is None:
            return None

        return ProtonDBInfo(**entry["data"])

    for attempt in range(MAX_RETRIES):
        response = requests.get(
            PROTONDB_SUMMARY_URL.format(app_id=app_id),
            timeout=15,
        )

        if response.status_code == 429:
            wait_time = 30 * (attempt + 1)

            print(
                f"  ProtonDB Rate-Limit erreicht. "
                f"Warte {wait_time} Sekunden..."
            )

            time.sleep(wait_time)
            continue

        if response.status_code == 404:
            cache[cache_key] = {
                "cached_at": datetime.now(UTC).isoformat(),
                "data": None,
            }

            save_json(CACHE_FILE, cache)

            time.sleep(REQUEST_DELAY)
            return None

        response.raise_for_status()

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

    print(f"  ProtonDB AppID {app_id}: nach mehreren Versuchen übersprungen.")
    return None