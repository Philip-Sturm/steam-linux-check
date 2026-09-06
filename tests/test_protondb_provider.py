import pytest
import requests

from steam_linux_check.models import ProtonDBInfo
from steam_linux_check.providers import protondb


def test_protondb_uses_stale_cache_on_network_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cached_data = {
        "123": {
            "cached_at": "2020-01-01T00:00:00+00:00",
            "data": {
                "app_id": 123,
                "tier": "gold",
                "confidence": "strong",
                "total_reports": 100,
                "best_reported_tier": "platinum",
                "trending_tier": "gold",
            },
        }
    }

    monkeypatch.setattr(
        protondb,
        "load_json",
        lambda _filename: cached_data,
    )

    def raise_network_error(*_args, **_kwargs):
        raise requests.ConnectionError(
            "Test network failure"
        )

    monkeypatch.setattr(
        protondb.requests,
        "get",
        raise_network_error,
    )

    info = protondb.get_protondb_info(123)

    assert info == ProtonDBInfo(
        app_id=123,
        tier="gold",
        confidence="strong",
        total_reports=100,
        best_reported_tier="platinum",
        trending_tier="gold",
    )


def test_protondb_returns_none_without_cache_on_network_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        protondb,
        "load_json",
        lambda _filename: {},
    )

    def raise_network_error(*_args, **_kwargs):
        raise requests.ConnectionError(
            "Test network failure"
        )

    monkeypatch.setattr(
        protondb.requests,
        "get",
        raise_network_error,
    )

    info = protondb.get_protondb_info(123)

    assert info is None

def test_protondb_updates_cache_on_successful_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cached_data = {
        "123": {
            "cached_at": "2020-01-01T00:00:00+00:00",
            "data": {
                "app_id": 123,
                "tier": "silver",
                "confidence": "strong",
                "total_reports": 20,
                "best_reported_tier": "gold",
                "trending_tier": "silver",
            },
        }
    }

    monkeypatch.setattr(
        protondb,
        "load_json",
        lambda _filename: cached_data,
    )

    saved_cache = {}

    def fake_save_json(
        filename: str,
        data: dict,
    ) -> None:
        saved_cache["filename"] = filename
        saved_cache["data"] = data

    monkeypatch.setattr(
        protondb,
        "save_json",
        fake_save_json,
    )

    monkeypatch.setattr(
        protondb.time,
        "sleep",
        lambda _seconds: None,
    )

    class FakeResponse:
        def __init__(self) -> None:
            self.status_code = 200
            self.headers: dict[str, str] = {}
    
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict:
            return {
                "tier": "gold",
                "confidence": "strong",
                "total": 150,
                "bestReportedTier": "platinum",
                "trendingTier": "gold",
            }

    monkeypatch.setattr(
        protondb.requests,
        "get",
        lambda *args, **kwargs: FakeResponse(),
    )

    info = protondb.get_protondb_info(123)

    assert info == ProtonDBInfo(
        app_id=123,
        tier="gold",
        confidence="strong",
        total_reports=150,
        best_reported_tier="platinum",
        trending_tier="gold",
    )

    assert saved_cache["filename"] == "protondb.json"

    cached_info = (
        saved_cache["data"]
        ["123"]
        ["data"]
    )

    assert cached_info == {
        "app_id": 123,
        "tier": "gold",
        "confidence": "strong",
        "total_reports": 150,
        "best_reported_tier": "platinum",
        "trending_tier": "gold",
    }