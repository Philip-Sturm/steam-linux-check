import pytest
import requests

from steam_linux_check.errors import ProviderUnavailableError
from steam_linux_check.models import SteamStoreInfo
from steam_linux_check.providers import steam_store


def test_steam_store_uses_stale_cache_on_network_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cached_data = {
        "620": {
            "cached_at": "2020-01-01T00:00:00+00:00",
            "data": {
                "app_id": 620,
                "name": "Portal 2",
                "app_type": "game",
                "windows": True,
                "mac": True,
                "linux": True,
            },
        }
    }

    monkeypatch.setattr(
        steam_store,
        "load_json",
        lambda _filename: cached_data,
    )

    def raise_network_error(*_args, **_kwargs):
        raise requests.ConnectionError(
            "Test network failure"
        )

    monkeypatch.setattr(
        steam_store.requests,
        "get",
        raise_network_error,
    )

    info = steam_store.get_app_details(620)

    assert info == SteamStoreInfo(
        app_id=620,
        name="Portal 2",
        app_type="game",
        windows=True,
        mac=True,
        linux=True,
    )


def test_steam_store_raises_without_cache_on_network_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        steam_store,
        "load_json",
        lambda _filename: {},
    )

    def raise_network_error(*_args, **_kwargs):
        raise requests.ConnectionError(
            "Test network failure"
        )

    monkeypatch.setattr(
        steam_store.requests,
        "get",
        raise_network_error,
    )

    with pytest.raises(
        ProviderUnavailableError,
    ) as error:
        steam_store.get_app_details(620)

    assert error.value.provider == "Steam Store"