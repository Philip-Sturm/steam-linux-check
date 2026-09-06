import requests

from ..models import AntiCheatInfo

ANTICHEAT_DATA_URL = (
    "https://raw.githubusercontent.com/"
    "AreWeAntiCheatYet/AreWeAntiCheatYet/master/games.json"
)


def get_anticheat_games() -> list[AntiCheatInfo]:
    """Fetch the AreWeAntiCheatYet game database."""

    response = requests.get(
        ANTICHEAT_DATA_URL,
        timeout=30,
    )

    response.raise_for_status()

    games = response.json()

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