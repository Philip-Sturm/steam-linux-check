import pytest
import requests

from steam_linux_check.models import SteamDeckInfo
from steam_linux_check.providers import steam_deck


def test_steam_deck_uses_stale_cache_on_network_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cached_data = {
        "620": {
            "cached_at": "2020-01-01T00:00:00+00:00",
            "data": {
                "app_id": 620,
                "deck_category": 3,
                "steamos_category": 2,
            },
        }
    }

    monkeypatch.setattr(
        steam_deck,
        "load_json",
        lambda _filename: cached_data,
    )

    def raise_network_error(*_args, **_kwargs):
        raise requests.ConnectionError(
            "Test network failure"
        )

    monkeypatch.setattr(
        steam_deck.requests,
        "get",
        raise_network_error,
    )

    info = steam_deck.get_steam_deck_info(620)

    assert info == SteamDeckInfo(
        app_id=620,
        deck_category=3,
        steamos_category=2,
    )


def test_steam_deck_returns_none_without_cache_on_network_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        steam_deck,
        "load_json",
        lambda _filename: {},
    )

    def raise_network_error(*_args, **_kwargs):
        raise requests.ConnectionError(
            "Test network failure"
        )

    monkeypatch.setattr(
        steam_deck.requests,
        "get",
        raise_network_error,
    )

    info = steam_deck.get_steam_deck_info(620)

    assert info is None