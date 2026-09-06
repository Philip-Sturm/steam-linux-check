import pytest
import requests

from steam_linux_check.errors import ProviderUnavailableError
from steam_linux_check.models import AntiCheatInfo
from steam_linux_check.providers import anticheat


def test_anticheat_uses_stale_cache_on_network_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cached_data = {
        "games": {
            "cached_at": "2020-01-01T00:00:00+00:00",
            "data": [
                {
                    "app_id": 578080,
                    "name": "PUBG",
                    "status": "Broken",
                    "anticheats": [
                        "BattlEye",
                    ],
                }
            ],
        }
    }

    monkeypatch.setattr(
        anticheat,
        "load_json",
        lambda _filename: cached_data,
    )

    def raise_network_error(*_args, **_kwargs):
        raise requests.ConnectionError(
            "Test network failure"
        )

    monkeypatch.setattr(
        anticheat.requests,
        "get",
        raise_network_error,
    )

    games = anticheat.get_anticheat_games()

    assert games == [
        AntiCheatInfo(
            app_id=578080,
            name="PUBG",
            status="Broken",
            anticheats=[
                "BattlEye",
            ],
        )
    ]


def test_anticheat_raises_without_cache_on_network_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        anticheat,
        "load_json",
        lambda _filename: {},
    )

    def raise_network_error(*_args, **_kwargs):
        raise requests.ConnectionError(
            "Test network failure"
        )

    monkeypatch.setattr(
        anticheat.requests,
        "get",
        raise_network_error,
    )

    with pytest.raises(
        ProviderUnavailableError,
    ) as error:
        anticheat.get_anticheat_games()

    assert error.value.provider == "Anti-Cheat"

def test_anticheat_caches_successful_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        anticheat,
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
        anticheat,
        "save_json",
        fake_save_json,
    )

    class FakeResponse:
        def __init__(self) -> None:
            self.status_code = 200
            self.headers: dict[str, str] = {}

        def raise_for_status(self) -> None:
            pass

        def json(self) -> list[dict]:
            return [
                {
                    "name": "Test Game",
                    "status": "Denied",
                    "anticheats": [
                        "BattlEye",
                    ],
                    "storeIds": {
                        "steam": "123456",
                    },
                }
            ]

    monkeypatch.setattr(
        anticheat.requests,
        "get",
        lambda *args, **kwargs: FakeResponse(),
    )

    games = anticheat.get_anticheat_games()

    assert games == [
        AntiCheatInfo(
            app_id=123456,
            name="Test Game",
            status="Denied",
            anticheats=[
                "BattlEye",
            ],
        )
    ]

    assert saved_cache["filename"] == "anticheat.json"

    assert (
        saved_cache["data"]
        ["games"]
        ["data"]
        == [
            {
                "app_id": 123456,
                "name": "Test Game",
                "status": "Denied",
                "anticheats": [
                    "BattlEye",
                ],
            }
        ]
    )