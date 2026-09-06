import time
from dataclasses import asdict
from datetime import UTC, datetime, timedelta

import requests

from ..cache import is_cache_entry_fresh, load_json, save_json
from ..models import AntiCheatInfo

ANTICHEAT_DATA_URL = (
    "https://raw.githubusercontent.com/"
    "AreWeAntiCheatYet/AreWeAntiCheatYet/master/games.json"
)

CACHE_FILE = "anticheat.json"
CACHE_KEY = "games"
CACHE_MAX_AGE = timedelta(days=7)

MAX_RETRIES = 4


def _load_cached_games(
    cache: dict,
) -> list[AntiCheatInfo] | None:
    """Load cached Anti-Cheat data regardless of its age."""

    entry = cache.get(CACHE_KEY)

    if not isinstance(entry, dict):
        return None

    data = entry.get("data")

    if not isinstance(data, list):
        return None

    try:
        return [
            AntiCheatInfo(**game)
            for game in data
        ]
    except (TypeError, ValueError):
        return None


def _parse_games(
    games: list[dict],
) -> list[AntiCheatInfo]:
    """Convert AreWeAntiCheatYet data into internal models."""

    results: list[AntiCheatInfo] = []

    for game in games:
        store_ids = game.get("storeIds", {})
        steam_id = store_ids.get("steam")

        app_id = None

        if steam_id is not None:
            try:
                app_id = int(steam_id)
            except (TypeError, ValueError):
                pass

        results.append(
            AntiCheatInfo(
                app_id=app_id,
                name=game.get("name", "Unknown"),
                status=game.get("status", "Unknown"),
                anticheats=game.get("anticheats", []),
            )
        )

    return results


def get_anticheat_games() -> list[AntiCheatInfo]:
    """Fetch Anti-Cheat data with cache and offline fallback."""

    cache = load_json(CACHE_FILE)
    entry = cache.get(CACHE_KEY)

    # Frischer Cache
    if (
        isinstance(entry, dict)
        and is_cache_entry_fresh(entry, CACHE_MAX_AGE)
    ):
        cached_games = _load_cached_games(cache)

        if cached_games is not None:
            return cached_games

    # Netzwerkabfrage
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(
                ANTICHEAT_DATA_URL,
                timeout=30,
            )

        except requests.RequestException:
            cached_games = _load_cached_games(cache)

            if cached_games is not None:
                print(
                    "Anti-Cheat-Daten nicht erreichbar "
                    "– alter Cache wird verwendet."
                )
                return cached_games

            print(
                "Anti-Cheat-Daten nicht erreichbar "
                "und kein Cache vorhanden."
            )

            return []

        # Rate Limit
        if response.status_code == 429:
            wait_time = 30 * (attempt + 1)

            print(
                "Anti-Cheat Rate-Limit erreicht. "
                f"Warte {wait_time} Sekunden..."
            )

            time.sleep(wait_time)
            continue

        # Temporärer Serverfehler
        if 500 <= response.status_code < 600:
            wait_time = 5 * (attempt + 1)

            print(
                f"Anti-Cheat Serverfehler "
                f"{response.status_code}. "
                f"Neuer Versuch in {wait_time} Sekunden..."
            )

            time.sleep(wait_time)
            continue

        # Andere HTTP-Fehler
        try:
            response.raise_for_status()

        except requests.HTTPError:
            cached_games = _load_cached_games(cache)

            if cached_games is not None:
                print(
                    "Anti-Cheat HTTP-Fehler "
                    "– alter Cache wird verwendet."
                )
                return cached_games

            print(
                f"Anti-Cheat HTTP-Fehler "
                f"{response.status_code} "
                "und kein Cache vorhanden."
            )

            return []

        # JSON lesen
        try:
            raw_games = response.json()

        except ValueError:
            cached_games = _load_cached_games(cache)

            if cached_games is not None:
                print(
                    "Ungültige Anti-Cheat-Antwort "
                    "– alter Cache wird verwendet."
                )
                return cached_games

            print(
                "Ungültige Anti-Cheat-Antwort "
                "und kein Cache vorhanden."
            )

            return []

        if not isinstance(raw_games, list):
            cached_games = _load_cached_games(cache)

            if cached_games is not None:
                return cached_games

            return []

        # Erfolgreiche Antwort
        games = _parse_games(raw_games)

        cache[CACHE_KEY] = {
            "cached_at": datetime.now(UTC).isoformat(),
            "data": [
                asdict(game)
                for game in games
            ],
        }

        save_json(CACHE_FILE, cache)

        return games

    # Alle Versuche ausgeschöpft
    cached_games = _load_cached_games(cache)

    if cached_games is not None:
        print(
            "Anti-Cheat-Daten konnten nicht aktualisiert werden "
            "– alter Cache wird verwendet."
        )
        return cached_games

    return []