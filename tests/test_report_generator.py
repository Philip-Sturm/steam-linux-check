from pathlib import Path

import pytest

from steam_linux_check import report_generator
from steam_linux_check.models import GameReportEntry, ReportChange


def test_html_report_contains_game_and_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_dir = tmp_path / "output"
    html_file = output_dir / "report.html"

    monkeypatch.setattr(
        report_generator,
        "OUTPUT_DIR",
        output_dir,
    )

    monkeypatch.setattr(
        report_generator,
        "HTML_REPORT_FILE",
        html_file,
    )

    entry = GameReportEntry(
        app_id=123,
        name="Test Game",
        status="Broken",
        reason="Anti-Cheat status: Denied",
        native_linux=False,
        protondb_tier="gold",
        protondb_confidence="strong",
        protondb_reports=100,
        protondb_trending="gold",
        steamos_status="Playable",
        anticheat_status="Denied",
        anticheats=["BattlEye"],
        installed=True,
    )

    change = ReportChange(
        app_id=123,
        name="Test Game",
        change_type="changed",
        old_status="Works",
        new_status="Broken",
        details=[
            "Anti-Cheat: Supported → Denied",
        ],
    )

    result = report_generator.write_html_report(
        entries=[entry],
        changes=[change],
    )

    assert result == html_file
    assert html_file.is_file()

    html_text = html_file.read_text(
        encoding="utf-8",
    )

    assert "Test Game" in html_text
    assert "Broken" in html_text
    assert "Works" in html_text
    assert "Anti-Cheat: Supported → Denied" in html_text
    assert "BattlEye" in html_text

def test_html_report_does_not_duplicate_status_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_dir = tmp_path / "output"
    html_file = output_dir / "report.html"

    monkeypatch.setattr(
        report_generator,
        "OUTPUT_DIR",
        output_dir,
    )

    monkeypatch.setattr(
        report_generator,
        "HTML_REPORT_FILE",
        html_file,
    )

    entry = GameReportEntry(
        app_id=123,
        name="Status Change Test Game",
        status="Broken",
        reason="Test reason",
        native_linux=False,
        protondb_tier="gold",
        protondb_confidence="strong",
        protondb_reports=100,
        protondb_trending="gold",
        steamos_status="Playable",
        anticheat_status=None,
        anticheats=[],
        installed=False,
    )

    change = ReportChange(
        app_id=123,
        name="Status Change Test Game",
        change_type="changed",
        old_status="Works",
        new_status="Broken",
        details=[],
    )

    report_generator.write_html_report(
        entries=[entry],
        changes=[change],
    )

    html_text = html_file.read_text(
        encoding="utf-8",
    )

    assert "Status Change Test Game" in html_text
    assert "Works" in html_text
    assert "Broken" in html_text

    # Ein reiner Statuswechsel darf nicht zusätzlich als
    # redundante Detailzeile dargestellt werden.
    assert "Status: Works → Broken" not in html_text