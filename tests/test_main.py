from pathlib import Path
from types import SimpleNamespace

import pytest

from steam_linux_check import cli as app_main


def test_main_returns_1_when_steam_is_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        app_main,
        "find_steam_installation",
        lambda: None,
    )

    assert app_main.main() == 1


def test_main_returns_1_when_steam_id_is_not_found(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        app_main,
        "find_steam_installation",
        lambda: tmp_path,
    )

    monkeypatch.setattr(
        app_main,
        "find_steam_user_id",
        lambda _steam_path: None,
    )

    assert app_main.main() == 1


def test_main_returns_1_when_owned_games_cannot_be_loaded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        app_main,
        "find_steam_installation",
        lambda: tmp_path,
    )

    monkeypatch.setattr(
        app_main,
        "find_steam_user_id",
        lambda _steam_path: "123456789",
    )

    monkeypatch.setattr(
        app_main,
        "load_previous_report",
        dict,
    )

    monkeypatch.setattr(
        app_main,
        "find_steam_libraries",
        lambda _steam_path: [],
    )

    monkeypatch.setattr(
        app_main,
        "find_installed_apps",
        lambda _libraries: [],
    )

    def raise_library_error(
        _steam_id: str,
    ) -> None:
        raise RuntimeError(
            "Test library failure"
        )

    monkeypatch.setattr(
        app_main,
        "get_owned_games",
        raise_library_error,
    )

    assert app_main.main() == 1


def test_main_returns_0_after_successful_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        app_main,
        "find_steam_installation",
        lambda: tmp_path,
    )

    monkeypatch.setattr(
        app_main,
        "find_steam_user_id",
        lambda _steam_path: "123456789",
    )

    monkeypatch.setattr(
        app_main,
        "load_previous_report",
        dict,
    )

    monkeypatch.setattr(
        app_main,
        "find_steam_libraries",
        lambda _steam_path: [],
    )

    monkeypatch.setattr(
        app_main,
        "find_installed_apps",
        lambda _libraries: [],
    )

    monkeypatch.setattr(
        app_main,
        "get_owned_games",
        lambda _steam_id: [],
    )

    provider_data = SimpleNamespace(
        store_info_by_app={},
        proton_info_by_app={},
        anticheat_by_app_id={},
        deck_info_by_app={},
        degraded_sources=set(),
    )

    monkeypatch.setattr(
        app_main,
        "collect_compatibility_data",
        lambda _owned_games: provider_data,
    )

    monkeypatch.setattr(
        app_main,
        "build_report_entries",
        lambda **_kwargs: ([], []),
    )

    monkeypatch.setattr(
        app_main,
        "write_json_report",
        lambda _entries: tmp_path / "report.json",
    )

    monkeypatch.setattr(
        app_main,
        "write_csv_report",
        lambda _entries: tmp_path / "report.csv",
    )

    html_call = {}

    def fake_write_html_report(
        _entries,
        changes=None,
        degraded_sources=None,
    ) -> Path:
        html_call["changes"] = changes
        html_call["degraded_sources"] = degraded_sources

        return tmp_path / "report.html"

    monkeypatch.setattr(
        app_main,
        "write_html_report",
        fake_write_html_report,
    )

    save_called = {
        "value": False,
    }

    def fake_save_current_report(
        _entries,
    ) -> None:
        save_called["value"] = True

    monkeypatch.setattr(
        app_main,
        "save_current_report",
        fake_save_current_report,
    )

    assert app_main.main() == 0

    assert save_called["value"] is True
    assert html_call["changes"] == []
    assert html_call["degraded_sources"] == set()


def test_main_does_not_save_state_when_provider_is_degraded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        app_main,
        "find_steam_installation",
        lambda: tmp_path,
    )

    monkeypatch.setattr(
        app_main,
        "find_steam_user_id",
        lambda _steam_path: "123456789",
    )

    monkeypatch.setattr(
        app_main,
        "load_previous_report",
        lambda: {
            123: {
                "app_id": 123,
                "name": "Previous Test Game",
                "status": "Works",
            }
        },
    )

    monkeypatch.setattr(
        app_main,
        "find_steam_libraries",
        lambda _steam_path: [],
    )

    monkeypatch.setattr(
        app_main,
        "find_installed_apps",
        lambda _libraries: [],
    )

    monkeypatch.setattr(
        app_main,
        "get_owned_games",
        lambda _steam_id: [],
    )

    provider_data = SimpleNamespace(
        store_info_by_app={},
        proton_info_by_app={},
        anticheat_by_app_id={},
        deck_info_by_app={},
        degraded_sources={"ProtonDB"},
    )

    monkeypatch.setattr(
        app_main,
        "collect_compatibility_data",
        lambda _owned_games: provider_data,
    )

    monkeypatch.setattr(
        app_main,
        "build_report_entries",
        lambda **_kwargs: ([], []),
    )

    def fail_if_compare_reports_is_called(
        _previous,
        _current,
    ):
        raise AssertionError(
            "compare_reports() darf bei einem "
            "degradierten Lauf nicht aufgerufen werden."
        )

    monkeypatch.setattr(
        app_main,
        "compare_reports",
        fail_if_compare_reports_is_called,
    )

    monkeypatch.setattr(
        app_main,
        "write_json_report",
        lambda _entries: tmp_path / "report.json",
    )

    monkeypatch.setattr(
        app_main,
        "write_csv_report",
        lambda _entries: tmp_path / "report.csv",
    )

    html_call = {}

    def fake_write_html_report(
        _entries,
        changes=None,
        degraded_sources=None,
    ) -> Path:
        html_call["changes"] = changes
        html_call["degraded_sources"] = degraded_sources

        return tmp_path / "report.html"

    monkeypatch.setattr(
        app_main,
        "write_html_report",
        fake_write_html_report,
    )

    save_called = {
        "value": False,
    }

    def fake_save_current_report(
        _entries,
    ) -> None:
        save_called["value"] = True

    monkeypatch.setattr(
        app_main,
        "save_current_report",
        fake_save_current_report,
    )

    assert app_main.main() == 0

    assert save_called["value"] is False
    assert html_call["changes"] == []
    assert html_call["degraded_sources"] == {
        "ProtonDB",
    }