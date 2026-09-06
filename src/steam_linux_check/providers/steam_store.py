import requests

from ..models import SteamStoreInfo

STEAM_APP_DETAILS_URL = "https://store.steampowered.com/api/appdetails"


def get_app_details(app_id: int) -> SteamStoreInfo | None:
    """Fetch Steam Store metadata for one app."""

    response = requests.get(
        STEAM_APP_DETAILS_URL,
        params={"appids": app_id},
        timeout=15,
    )

    response.raise_for_status()

    result = response.json().get(str(app_id))

    if not result or not result.get("success"):
        return None

    data = result["data"]
    platforms = data.get("platforms", {})

    return SteamStoreInfo(
        app_id=app_id,
        name=data.get("name", "Unknown"),
        app_type=data.get("type", "unknown"),
        windows=platforms.get("windows", False),
        mac=platforms.get("mac", False),
        linux=platforms.get("linux", False),
    )