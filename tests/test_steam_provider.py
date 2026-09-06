import pytest
import requests

from steam_linux_check.models import OwnedGame
from steam_linux_check.providers import steam


def test_get_owned_games_uses_cache_on_network_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "STEAM_API_KEY",
        "test-key",
    )

    cached_data = {
        "123456789": {
            "cached_at": "2026-01-01T00:00:00+00:00",
            "data": [
                {
                    "app_id": 620,
                    "name": "Portal 2",
                }
            ],
        }
    }

    monkeypatch.setattr(
        steam,
        "load_json",
        lambda _filename: cached_data,
    )

    def raise_network_error(*args, **kwargs):
        raise requests.ConnectionError(
            "Test network failure"
        )

    monkeypatch.setattr(
        steam.requests,
        "get",
        raise_network_error,
    )

    games = steam.get_owned_games(
        "123456789"
    )

    assert games == [
        OwnedGame(
            app_id=620,
            name="Portal 2",
        )
    ]


def test_get_owned_games_raises_without_cache_on_network_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "STEAM_API_KEY",
        "test-key",
    )

    monkeypatch.setattr(
        steam,
        "load_json",
        lambda _filename: {},
    )

    def raise_network_error(*args, **kwargs):
        raise requests.ConnectionError(
            "Test network failure"
        )

    monkeypatch.setattr(
        steam.requests,
        "get",
        raise_network_error,
    )

    with pytest.raises(
        RuntimeError,
        match="keine gecachte Bibliothek",
    ):
        steam.get_owned_games(
            "123456789"
        )


def test_get_owned_games_caches_successful_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "STEAM_API_KEY",
        "test-key",
    )

    monkeypatch.setattr(
        steam,
        "load_json",
        lambda _filename: {},
    )

    saved_cache = {}

    def fake_save_json(
        filename: str,
        data: dict,
    ) -> None:
        saved_cache["filename"] = filename
        saved_cache["data"] = data

    monkeypatch.setattr(
        steam,
        "save_json",
        fake_save_json,
    )

    class FakeResponse:
        def __init__(self) -> None:
            self.status_code = 200
            self.headers: dict[str, str] = {}
    
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict:
            return {
                "response": {
                    "games": [
                        {
                            "appid": 620,
                            "name": "Portal 2",
                        },
                        {
                            "appid": 400,
                            "name": "Portal",
                        },
                    ]
                }
            }

    monkeypatch.setattr(
        steam.requests,
        "get",
        lambda *args, **kwargs: FakeResponse(),
    )

    games = steam.get_owned_games(
        "123456789"
    )

    assert games == [
        OwnedGame(
            app_id=620,
            name="Portal 2",
        ),
        OwnedGame(
            app_id=400,
            name="Portal",
        ),
    ]

    assert (
        saved_cache["filename"]
        == "steam_owned_games.json"
    )

    cached_games = (
        saved_cache["data"]
        ["123456789"]
        ["data"]
    )

    assert cached_games == [
        {
            "app_id": 620,
            "name": "Portal 2",
        },
        {
            "app_id": 400,
            "name": "Portal",
        },
    ]