import os
import time
from dataclasses import asdict
from datetime import UTC, datetime

import requests
from dotenv import load_dotenv

from ..cache import load_json, save_json
from ..models import OwnedGame

STEAM_OWNED_GAMES_URL = (
    "https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/"
)

CACHE_FILE = "steam_owned_games.json"

MAX_RETRIES = 4


def _load_cached_games(
    cache: dict,
    steam_id: str,
) -> list[OwnedGame] | None:
    """Load the last known Steam library from cache."""

    entry = cache.get(steam_id)

    if not isinstance(entry, dict):
        return None

    data = entry.get("data")

    if not isinstance(data, list):
        return None

    try:
        return [
            OwnedGame(**game)
            for game in data
        ]
    except (TypeError, ValueError):
        return None


def get_owned_games(steam_id: str) -> list[OwnedGame]:
    """Fetch owned Steam games with offline cache fallback."""

    load_dotenv()

    api_key = os.getenv("STEAM_API_KEY")

    if not api_key:
        raise RuntimeError(
            "STEAM_API_KEY fehlt in der .env-Datei."
        )

    cache = load_json(CACHE_FILE)

    # Die Besitzbibliothek wird bewusst bei jedem Lauf
    # neu abgefragt. Der Cache dient nur als Fallback.
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(
                STEAM_OWNED_GAMES_URL,
                params={
                    "key": api_key,
                    "steamid": steam_id,
                    "include_appinfo": True,
                    "include_played_free_games": True,
                },
                timeout=15,
            )

        except requests.RequestException:
            cached_games = _load_cached_games(
                cache,
                steam_id,
            )

            if cached_games is not None:
                print(
                    "Steam Web API nicht erreichbar "
                    "– letzte bekannte Bibliothek wird verwendet."
                )
                return cached_games

            raise RuntimeError(
                "Steam Web API nicht erreichbar und "
                "keine gecachte Bibliothek vorhanden."
            )

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
                "Steam Web API Rate-Limit erreicht. "
                f"Warte {wait_time} Sekunden..."
            )

            time.sleep(wait_time)
            continue

        # Temporärer Steam-Serverfehler
        if 500 <= response.status_code < 600:
            wait_time = 5 * (attempt + 1)

            print(
                f"Steam Web API Serverfehler "
                f"{response.status_code}. "
                f"Neuer Versuch in {wait_time} Sekunden..."
            )

            time.sleep(wait_time)
            continue

        # Andere HTTP-Fehler
        try:
            response.raise_for_status()

        except requests.HTTPError:
            cached_games = _load_cached_games(
                cache,
                steam_id,
            )

            if cached_games is not None:
                print(
                    f"Steam Web API HTTP-Fehler "
                    f"{response.status_code} "
                    "– letzte bekannte Bibliothek wird verwendet."
                )
                return cached_games

            raise RuntimeError(
                f"Steam Web API HTTP-Fehler "
                f"{response.status_code} und "
                "keine gecachte Bibliothek vorhanden."
            )

        # JSON lesen
        try:
            data = response.json()

        except ValueError:
            cached_games = _load_cached_games(
                cache,
                steam_id,
            )

            if cached_games is not None:
                print(
                    "Ungültige Steam-API-Antwort "
                    "– letzte bekannte Bibliothek wird verwendet."
                )
                return cached_games

            raise RuntimeError(
                "Ungültige Steam-API-Antwort und "
                "keine gecachte Bibliothek vorhanden."
            )

        response_data = data.get("response")

        if not isinstance(response_data, dict):
            cached_games = _load_cached_games(
                cache,
                steam_id,
            )

            if cached_games is not None:
                return cached_games

            raise RuntimeError(
                "Steam Web API lieferte keine "
                "verwertbaren Bibliotheksdaten."
            )

        raw_games = response_data.get("games", [])

        if not isinstance(raw_games, list):
            raise TypeError(
                "Steam Web API lieferte ein "
                "unerwartetes Datenformat."
            )

        games = [
            OwnedGame(
                app_id=game["appid"],
                name=game.get("name", "Unknown"),
            )
            for game in raw_games
            if "appid" in game
        ]

        # Erfolgreiche Bibliothek lokal sichern
        cache[steam_id] = {
            "cached_at": datetime.now(UTC).isoformat(),
            "data": [
                asdict(game)
                for game in games
            ],
        }

        save_json(CACHE_FILE, cache)

        return games

    # Alle Versuche ausgeschöpft
    cached_games = _load_cached_games(
        cache,
        steam_id,
    )

    if cached_games is not None:
        print(
            "Steam Web API konnte nicht aktualisiert werden "
            "– letzte bekannte Bibliothek wird verwendet."
        )
        return cached_games

    raise RuntimeError(
        "Steam-Bibliothek konnte nicht geladen werden "
        "und es ist kein Cache vorhanden."
    )