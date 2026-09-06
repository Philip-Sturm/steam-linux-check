import json
from dataclasses import asdict
from pathlib import Path

from .models import GameReportEntry, ReportChange

STATE_DIR = Path("state")
PREVIOUS_REPORT_FILE = STATE_DIR / "previous_report.json"


def load_previous_report() -> dict[int, dict]:
    """Load the previous compatibility state."""

    if not PREVIOUS_REPORT_FILE.is_file():
        return {}

    data = json.loads(
        PREVIOUS_REPORT_FILE.read_text(encoding="utf-8")
    )

    return {
        int(entry["app_id"]): entry
        for entry in data.get("games", [])
    }

def compare_reports(
    previous: dict[int, dict],
    current: list[GameReportEntry],
) -> list[ReportChange]:
    """Compare the previous and current compatibility reports."""

    changes: list[ReportChange] = []

    current_by_app = {
        entry.app_id: entry
        for entry in current
    }

    # Neue oder geänderte Spiele
    for app_id, entry in current_by_app.items():
        old = previous.get(app_id)

        if old is None:
            changes.append(
                ReportChange(
                    app_id=app_id,
                    name=entry.name,
                    change_type="added",
                    old_status=None,
                    new_status=entry.status,
                    details=["New game in Steam library"],
                )
            )
            continue

        details: list[str] = []

        old_status = old.get("status")
        new_status = entry.status

        status_changed = old_status != new_status

        if old.get("protondb_tier") != entry.protondb_tier:
            details.append(
                "ProtonDB: "
                f"{old.get('protondb_tier')} → "
                f"{entry.protondb_tier}"
            )

        if old.get("protondb_trending") != entry.protondb_trending:
            details.append(
                "ProtonDB trending: "
                f"{old.get('protondb_trending')} → "
                f"{entry.protondb_trending}"
            )

        if old.get("anticheat_status") != entry.anticheat_status:
            details.append(
                "Anti-Cheat: "
                f"{old.get('anticheat_status')} → "
                f"{entry.anticheat_status}"
            )

        if old.get("steamos_status") != entry.steamos_status:
            details.append(
                "SteamOS: "
                f"{old.get('steamos_status')} → "
                f"{entry.steamos_status}"
            )

        if old.get("installed") != entry.installed:
            details.append(
                "Installed: "
                f"{old.get('installed')} → "
                f"{entry.installed}"
            )

        if status_changed or details:
            changes.append(
                ReportChange(
                    app_id=app_id,
                    name=entry.name,
                    change_type="changed",
                    old_status=old_status,
                    new_status=new_status,
                    details=details,
                )
            )

    # Spiele, die nicht mehr in der Besitzbibliothek vorkommen
    for app_id, old in previous.items():
        if app_id not in current_by_app:
            changes.append(
                ReportChange(
                    app_id=app_id,
                    name=old.get("name", "Unknown"),
                    change_type="removed",
                    old_status=old.get("status"),
                    new_status=None,
                    details=["Game no longer present in Steam library"],
                )
            )

    return changes


def save_current_report(entries: list[GameReportEntry]) -> None:
    """Save the current compatibility state for the next run."""

    STATE_DIR.mkdir(parents=True, exist_ok=True)

    data = {
        "games": [
            asdict(entry)
            for entry in entries
        ]
    }

    PREVIOUS_REPORT_FILE.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )