import os

import requests
from dotenv import load_dotenv

from ..models import OwnedGame

STEAM_OWNED_GAMES_URL = (
    "https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/"
)


def get_owned_games(steam_id: str) -> list[OwnedGame]:
    """Fetch the user's owned Steam games."""

    load_dotenv()

    api_key = os.getenv("STEAM_API_KEY")

    if not api_key:
        raise RuntimeError("STEAM_API_KEY fehlt in der .env-Datei.")

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

    response.raise_for_status()

    data = response.json()

    games = data.get("response", {}).get("games", [])

    return [
        OwnedGame(
            app_id=game["appid"],
            name=game.get("name", "Unknown"),
        )
        for game in games
    ]