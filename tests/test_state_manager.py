from dataclasses import asdict

from steam_linux_check.models import GameReportEntry
from steam_linux_check.state_manager import compare_reports


def make_entry(
    *,
    status: str = "Works",
    protondb_tier: str | None = "gold",
    protondb_trending: str | None = "gold",
    steamos_status: str | None = "Playable",
    anticheat_status: str | None = None,
    installed: bool = False,
) -> GameReportEntry:
    return GameReportEntry(
        app_id=123,
        name="Test Game",
        status=status,
        reason="Test reason",
        native_linux=False,
        protondb_tier=protondb_tier,
        protondb_confidence="strong",
        protondb_reports=100,
        protondb_trending=protondb_trending,
        steamos_status=steamos_status,
        anticheat_status=anticheat_status,
        anticheats=[],
        installed=installed,
    )


def test_compare_reports_returns_no_changes_for_identical_entry() -> None:
    entry = make_entry()

    previous = {
        entry.app_id: asdict(entry),
    }

    changes = compare_reports(
        previous,
        [entry],
    )

    assert changes == []


def test_compare_reports_detects_status_change() -> None:
    old_entry = make_entry(
        status="Works",
    )

    new_entry = make_entry(
        status="Broken",
    )

    previous = {
        old_entry.app_id: asdict(old_entry),
    }

    changes = compare_reports(
        previous,
        [new_entry],
    )

    assert len(changes) == 1

    change = changes[0]

    assert change.app_id == 123
    assert change.name == "Test Game"
    assert change.old_status == "Works"
    assert change.new_status == "Broken"
    assert change.details == []


def test_compare_reports_detects_installation_change() -> None:
    old_entry = make_entry(
        installed=False,
    )

    new_entry = make_entry(
        installed=True,
    )

    previous = {
        old_entry.app_id: asdict(old_entry),
    }

    changes = compare_reports(
        previous,
        [new_entry],
    )

    assert len(changes) == 1

    change = changes[0]

    assert change.app_id == 123
    assert change.name == "Test Game"
    assert change.old_status == "Works"
    assert change.new_status == "Works"
    assert change.details


def test_compare_reports_detects_protondb_change() -> None:
    old_entry = make_entry(
        protondb_tier="silver",
        protondb_trending="silver",
    )

    new_entry = make_entry(
        protondb_tier="gold",
        protondb_trending="gold",
    )

    previous = {
        old_entry.app_id: asdict(old_entry),
    }

    changes = compare_reports(
        previous,
        [new_entry],
    )

    assert len(changes) == 1

    change = changes[0]

    assert any(
        "ProtonDB" in detail
        and "silver" in detail
        and "gold" in detail
        for detail in change.details
    )

def test_compare_reports_detects_added_game() -> None:
    new_entry = make_entry()

    changes = compare_reports(
        previous={},
        current=[new_entry],
    )

    assert len(changes) == 1

    change = changes[0]

    assert change.app_id == 123
    assert change.name == "Test Game"
    assert change.change_type == "added"
    assert change.old_status is None
    assert change.new_status == "Works"


def test_compare_reports_detects_removed_game() -> None:
    old_entry = make_entry()

    previous = {
        old_entry.app_id: asdict(old_entry),
    }

    changes = compare_reports(
        previous=previous,
        current=[],
    )

    assert len(changes) == 1

    change = changes[0]

    assert change.app_id == 123
    assert change.name == "Test Game"
    assert change.change_type == "removed"
    assert change.old_status == "Works"
    assert change.new_status is None

def test_compare_reports_groups_multiple_changes_for_same_game() -> None:
    old_entry = make_entry(
        status="Works",
        protondb_tier="gold",
        protondb_trending="gold",
        installed=False,
    )

    new_entry = make_entry(
        status="Broken",
        protondb_tier="bronze",
        protondb_trending="borked",
        installed=True,
    )

    previous = {
        old_entry.app_id: asdict(old_entry),
    }

    changes = compare_reports(
        previous=previous,
        current=[new_entry],
    )

    assert len(changes) == 1

    change = changes[0]

    assert change.app_id == 123
    assert change.name == "Test Game"
    assert change.old_status == "Works"
    assert change.new_status == "Broken"

    assert len(change.details) >= 3