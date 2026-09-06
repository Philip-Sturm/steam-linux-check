from pathlib import Path
from types import SimpleNamespace

import pytest

import main as app_main


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

    def raise_library_error(_steam_id: str):
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

    monkeypatch.setattr(
        app_main,
        "write_html_report",
        lambda _entries, changes=None: tmp_path / "report.html",
    )

    monkeypatch.setattr(
        app_main,
        "save_current_report",
        lambda _entries: None,
    )

    assert app_main.main() == 0