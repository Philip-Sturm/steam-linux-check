import csv
import html
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from .models import GameReportEntry, ReportChange

OUTPUT_DIR = Path("output")

JSON_REPORT_FILE = OUTPUT_DIR / "report.json"
CSV_REPORT_FILE = OUTPUT_DIR / "report.csv"
HTML_REPORT_FILE = OUTPUT_DIR / "report.html"


def write_json_report(
    entries: list[GameReportEntry],
) -> Path:
    """Write the compatibility report as JSON."""

    JSON_REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    data = {
        "generated_at": datetime.now(UTC).isoformat(),
        "total_games": len(entries),
        "games": [
            asdict(entry)
            for entry in entries
        ],
    }

    JSON_REPORT_FILE.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return JSON_REPORT_FILE


def write_csv_report(
    entries: list[GameReportEntry],
) -> Path:
    """Write the compatibility report as CSV."""

    CSV_REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "app_id",
        "name",
        "status",
        "reason",
        "native_linux",
        "protondb_tier",
        "protondb_confidence",
        "protondb_reports",
        "protondb_trending",
        "steamos_status",
        "anticheat_status",
        "anticheats",
        "installed",
    ]

    with CSV_REPORT_FILE.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for entry in entries:
            writer.writerow(
                {
                    "app_id": entry.app_id,
                    "name": entry.name,
                    "status": entry.status,
                    "reason": entry.reason,
                    "native_linux": entry.native_linux,
                    "protondb_tier": entry.protondb_tier,
                    "protondb_confidence": entry.protondb_confidence,
                    "protondb_reports": entry.protondb_reports,
                    "protondb_trending": entry.protondb_trending,
                    "steamos_status": entry.steamos_status,
                    "anticheat_status": entry.anticheat_status,
                    "anticheats": ", ".join(
                        entry.anticheats
                    ),
                    "installed": entry.installed,
                }
            )

    return CSV_REPORT_FILE


def write_html_report(
    entries: list[GameReportEntry],
    changes: list[ReportChange] | None = None,
    degraded_sources: set[str] | None = None,
) -> Path:
    """Write an interactive HTML compatibility dashboard."""

    HTML_REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    changes = changes or []
    degraded_sources = degraded_sources or set()

    generated_at = datetime.now().astimezone().strftime(
        "%d.%m.%Y %H:%M"
    )

    # ---------------------------------------------------------
    # Statistiken
    # ---------------------------------------------------------

    total_count = len(entries)

    native_count = sum(
        entry.status == "Native"
        for entry in entries
    )

    works_count = sum(
        entry.status == "Works"
        for entry in entries
    )

    partial_count = sum(
        entry.status == "Partial"
        for entry in entries
    )

    broken_count = sum(
        entry.status == "Broken"
        for entry in entries
    )

    unknown_count = sum(
        entry.status == "Unknown"
        for entry in entries
    )

    installed_count = sum(
        entry.installed
        for entry in entries
    )

    # ---------------------------------------------------------
    # Degraded-Warnung
    # ---------------------------------------------------------

    degraded_banner = ""

    if degraded_sources:
        source_names = ", ".join(
            html.escape(source)
            for source in sorted(degraded_sources)
        )

        degraded_banner = f"""
        <section class="warning-banner">
            <strong>Unvollständiger Check</strong>

            <div>
                Folgende Datenquellen waren nicht vollständig verfügbar:
                {source_names}
            </div>

            <div>
                Der Änderungsvergleich wurde übersprungen und der letzte
                vollständige Vergleichszustand wurde nicht überschrieben.
            </div>
        </section>
        """

    # ---------------------------------------------------------
    # Änderungsbereich
    # ---------------------------------------------------------

    change_items: list[str] = []

    for change in changes:
        status_change = ""

        if (
            change.old_status is not None
            and change.new_status is not None
            and change.old_status != change.new_status
        ):
            status_change = f"""
            <div class="change-status">
                <span class="old-value">
                    {html.escape(change.old_status)}
                </span>

                <span class="change-arrow">
                    →
                </span>

                <span class="new-value">
                    {html.escape(change.new_status)}
                </span>
            </div>
            """

        details_html = ""

        if change.details:
            detail_items = "".join(
                f"<li>{html.escape(detail)}</li>"
                for detail in change.details
            )

            details_html = f"""
            <ul class="change-details">
                {detail_items}
            </ul>
            """

        change_type_labels = {
            "added": "Neu",
            "removed": "Entfernt",
            "changed": "Geändert",
        }

        change_label = change_type_labels.get(
            change.change_type,
            change.change_type,
        )

        change_items.append(
            f"""
            <article class="change-item">
                <div class="change-header">
                    <div>
                        <strong>
                            {html.escape(change.name)}
                        </strong>

                        <span class="change-appid">
                            AppID {change.app_id}
                        </span>
                    </div>

                    <span class="change-type">
                        {html.escape(change_label)}
                    </span>
                </div>

                {status_change}
                {details_html}
            </article>
            """
        )

    if degraded_sources:
        changes_content = """
        <div class="change-empty">
            Änderungsvergleich für diesen Lauf übersprungen.
        </div>
        """

    elif change_items:
        changes_content = "".join(change_items)

    else:
        changes_content = """
        <div class="change-empty">
            Keine Änderungen seit der letzten Prüfung.
        </div>
        """

    # ---------------------------------------------------------
    # Tabellenzeilen
    # ---------------------------------------------------------

    rows: list[str] = []

    for entry in entries:
        status_class = (
            entry.status
            .lower()
            .replace(" ", "-")
        )

        native_text = (
            "Ja"
            if entry.native_linux
            else "Nein"
        )

        installed_text = (
            "Ja"
            if entry.installed
            else "Nein"
        )

        protondb_tier = (
            entry.protondb_tier
            if entry.protondb_tier is not None
            else "—"
        )

        protondb_reports = (
            str(entry.protondb_reports)
            if entry.protondb_reports is not None
            else "—"
        )

        protondb_trending = (
            entry.protondb_trending
            if entry.protondb_trending is not None
            else "—"
        )

        steamos_status = (
            entry.steamos_status
            if entry.steamos_status is not None
            else "—"
        )

        anticheat_status = (
            entry.anticheat_status
            if entry.anticheat_status is not None
            else "—"
        )

        anticheats = (
            ", ".join(entry.anticheats)
            if entry.anticheats
            else "—"
        )

        rows.append(
            f"""
            <tr
                data-status="{html.escape(entry.status)}"
                data-installed="{str(entry.installed).lower()}"
            >
                <td class="appid">
                    {entry.app_id}
                </td>

                <td class="game-name">
                    {html.escape(entry.name)}
                </td>

                <td>
                    <span class="status-pill status-{status_class}">
                        {html.escape(entry.status)}
                    </span>
                </td>

                <td class="reason">
                    {html.escape(entry.reason)}
                </td>

                <td>
                    {native_text}
                </td>

                <td>
                    {html.escape(protondb_tier)}
                </td>

                <td>
                    {html.escape(protondb_reports)}
                </td>

                <td>
                    {html.escape(protondb_trending)}
                </td>

                <td>
                    {html.escape(steamos_status)}
                </td>

                <td>
                    {html.escape(anticheat_status)}
                </td>

                <td>
                    {html.escape(anticheats)}
                </td>

                <td>
                    {installed_text}
                </td>
            </tr>
            """
        )

    rows_html = "".join(rows)

    # ---------------------------------------------------------
    # HTML
    # ---------------------------------------------------------

    report = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="utf-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1"
    >

    <title>Steam Linux Compatibility Report</title>

    <style>
        :root {{
            color-scheme: dark;

            --bg: #07111f;
            --bg-secondary: #0b1728;
            --panel: #101f33;
            --panel-hover: #142842;
            --border: #233b58;

            --text: #e8eef7;
            --text-muted: #91a4bc;

            --native: #38d996;
            --works: #63d48d;
            --partial: #e5b84d;
            --broken: #ef6a73;
            --unknown: #8796aa;

            --accent: #6ba7ff;
        }}

        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;

            background:
                radial-gradient(
                    circle at top,
                    #10284a 0,
                    var(--bg) 38rem
                );

            color: var(--text);

            font-family:
                Inter,
                system-ui,
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                sans-serif;
        }}

        .container {{
            width: min(1600px, calc(100% - 32px));
            margin: 0 auto;
            padding: 38px 0 60px;
        }}

        .hero {{
            margin-bottom: 24px;
        }}

        .hero h1 {{
            margin: 0 0 8px;

            font-size: clamp(
                1.8rem,
                4vw,
                2.8rem
            );

            line-height: 1.1;
        }}

        .hero p {{
            margin: 0;
            color: var(--text-muted);
        }}

        .warning-banner {{
            margin: 0 0 24px;
            padding: 16px 18px;

            border: 1px solid #8a6925;
            border-radius: 12px;

            background:
                rgba(138, 105, 37, 0.18);

            line-height: 1.5;
        }}

        .warning-banner strong {{
            display: block;
            margin-bottom: 6px;
            font-size: 1.05rem;
        }}

        .cards {{
            display: grid;

            grid-template-columns:
                repeat(
                    auto-fit,
                    minmax(150px, 1fr)
                );

            gap: 12px;
            margin-bottom: 24px;
        }}

        .card {{
            padding: 18px;

            border: 1px solid var(--border);
            border-radius: 14px;

            background:
                rgba(16, 31, 51, 0.88);

            box-shadow:
                0 10px 30px
                rgba(0, 0, 0, 0.12);
        }}

        .card-label {{
            margin-bottom: 8px;

            color: var(--text-muted);

            font-size: 0.83rem;
            font-weight: 600;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }}

        .card-value {{
            font-size: 1.8rem;
            font-weight: 750;
        }}

        .changes-panel {{
            margin-bottom: 24px;

            border: 1px solid var(--border);
            border-radius: 14px;

            background:
                rgba(16, 31, 51, 0.9);

            overflow: hidden;
        }}

        .changes-panel summary {{
            padding: 16px 18px;

            cursor: pointer;
            user-select: none;

            font-weight: 700;
        }}

        .changes-content {{
            padding:
                0
                18px
                18px;
        }}

        .change-item {{
            padding: 14px 0;

            border-top:
                1px solid
                var(--border);
        }}

        .change-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;

            gap: 12px;
        }}

        .change-appid {{
            margin-left: 8px;

            color: var(--text-muted);

            font-size: 0.8rem;
        }}

        .change-type {{
            padding: 4px 9px;

            border:
                1px solid
                var(--border);

            border-radius: 999px;

            color: var(--text-muted);

            font-size: 0.75rem;
        }}

        .change-status {{
            display: flex;
            align-items: center;

            gap: 8px;

            margin-top: 10px;

            font-weight: 700;
        }}

        .old-value {{
            color: var(--text-muted);
        }}

        .new-value {{
            color: var(--text);
        }}

        .change-arrow {{
            color: var(--accent);
        }}

        .change-details {{
            margin:
                10px
                0
                0
                18px;

            padding: 0;

            color: var(--text-muted);
        }}

        .change-empty {{
            padding-top: 4px;
            color: var(--text-muted);
        }}

        .controls {{
            display: flex;
            flex-wrap: wrap;
            align-items: center;

            gap: 12px;

            margin-bottom: 16px;
        }}

        .search {{
            flex: 1 1 300px;

            min-width: 220px;

            padding: 11px 13px;

            border: 1px solid var(--border);
            border-radius: 10px;

            background: var(--bg-secondary);
            color: var(--text);

            outline: none;
        }}

        .search:focus {{
            border-color: var(--accent);
        }}

        .filters {{
            display: flex;
            flex-wrap: wrap;
            gap: 7px;
        }}

        .filter-button {{
            padding: 8px 11px;

            border: 1px solid var(--border);
            border-radius: 999px;

            background: var(--panel);
            color: var(--text);

            cursor: pointer;
        }}

        .filter-button:hover {{
            background: var(--panel-hover);
        }}

        .filter-button.active {{
            border-color: var(--accent);
            background: #17345a;
        }}

        .installed-filter {{
            display: inline-flex;
            align-items: center;

            gap: 8px;

            color: var(--text-muted);

            font-size: 0.9rem;
        }}

        .table-wrapper {{
            border: 1px solid var(--border);
            border-radius: 14px;

            background:
                rgba(11, 23, 40, 0.94);

            overflow: auto;

            box-shadow:
                0 12px 34px
                rgba(0, 0, 0, 0.14);
        }}

        table {{
            width: 100%;
            min-width: 1500px;

            border-collapse: collapse;
        }}

        thead {{
            position: sticky;
            top: 0;
            z-index: 2;

            background: #102038;
        }}

        th {{
            padding: 13px 12px;

            border-bottom:
                1px solid
                var(--border);

            color: var(--text-muted);

            font-size: 0.76rem;
            font-weight: 700;

            letter-spacing: 0.04em;
            text-align: left;
            text-transform: uppercase;

            white-space: nowrap;
        }}

        td {{
            padding: 12px;

            border-bottom:
                1px solid
                rgba(35, 59, 88, 0.7);

            vertical-align: top;
        }}

        tbody tr:hover {{
            background:
                rgba(107, 167, 255, 0.055);
        }}

        tbody tr:last-child td {{
            border-bottom: none;
        }}

        .appid {{
            color: var(--text-muted);
            font-variant-numeric: tabular-nums;
        }}

        .game-name {{
            min-width: 210px;
            font-weight: 650;
        }}

        .reason {{
            min-width: 250px;
            color: var(--text-muted);
        }}

        .status-pill {{
            display: inline-block;

            padding: 4px 9px;

            border-radius: 999px;

            font-size: 0.78rem;
            font-weight: 750;

            white-space: nowrap;
        }}

        .status-native {{
            background:
                rgba(56, 217, 150, 0.14);

            color: var(--native);
        }}

        .status-works {{
            background:
                rgba(99, 212, 141, 0.14);

            color: var(--works);
        }}

        .status-partial {{
            background:
                rgba(229, 184, 77, 0.14);

            color: var(--partial);
        }}

        .status-broken {{
            background:
                rgba(239, 106, 115, 0.14);

            color: var(--broken);
        }}

        .status-unknown {{
            background:
                rgba(135, 150, 170, 0.14);

            color: var(--unknown);
        }}

        .hidden {{
            display: none;
        }}

        .result-count {{
            margin-top: 12px;

            color: var(--text-muted);

            font-size: 0.85rem;
        }}

        @media (max-width: 700px) {{
            .container {{
                width: min(
                    100% - 20px,
                    1600px
                );

                padding-top: 24px;
            }}

            .cards {{
                grid-template-columns:
                    repeat(
                        2,
                        minmax(0, 1fr)
                    );
            }}
        }}
    </style>
</head>

<body>
    <main class="container">
        <section class="hero">
            <h1>
                Steam Linux Compatibility
            </h1>

            <p>
                {total_count} Spiele geprüft ·
                Erstellt am {html.escape(generated_at)}
            </p>
        </section>

        {degraded_banner}

        <section class="cards">
            <article class="card">
                <div class="card-label">
                    Gesamt
                </div>

                <div class="card-value">
                    {total_count}
                </div>
            </article>

            <article class="card">
                <div class="card-label">
                    Native
                </div>

                <div class="card-value">
                    {native_count}
                </div>
            </article>

            <article class="card">
                <div class="card-label">
                    Works
                </div>

                <div class="card-value">
                    {works_count}
                </div>
            </article>

            <article class="card">
                <div class="card-label">
                    Partial
                </div>

                <div class="card-value">
                    {partial_count}
                </div>
            </article>

            <article class="card">
                <div class="card-label">
                    Broken
                </div>

                <div class="card-value">
                    {broken_count}
                </div>
            </article>

            <article class="card">
                <div class="card-label">
                    Unknown
                </div>

                <div class="card-value">
                    {unknown_count}
                </div>
            </article>

            <article class="card">
                <div class="card-label">
                    Installiert
                </div>

                <div class="card-value">
                    {installed_count}
                </div>
            </article>
        </section>

        <details
            class="changes-panel"
            open
        >
            <summary>
                Änderungen seit letzter Prüfung:
                {len(changes)}
            </summary>

            <div class="changes-content">
                {changes_content}
            </div>
        </details>

        <section class="controls">
            <input
                id="search"
                class="search"
                type="search"
                placeholder="Spiel, AppID, Grund, ProtonDB, Anti-Cheat …"
                autocomplete="off"
            >

            <div class="filters">
                <button
                    class="filter-button active"
                    data-filter="All"
                    type="button"
                >
                    Alle
                </button>

                <button
                    class="filter-button"
                    data-filter="Native"
                    type="button"
                >
                    Native
                </button>

                <button
                    class="filter-button"
                    data-filter="Works"
                    type="button"
                >
                    Works
                </button>

                <button
                    class="filter-button"
                    data-filter="Partial"
                    type="button"
                >
                    Partial
                </button>

                <button
                    class="filter-button"
                    data-filter="Broken"
                    type="button"
                >
                    Broken
                </button>

                <button
                    class="filter-button"
                    data-filter="Unknown"
                    type="button"
                >
                    Unknown
                </button>
            </div>

            <label class="installed-filter">
                <input
                    id="installed-only"
                    type="checkbox"
                >

                Nur installiert
            </label>
        </section>

        <section class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th>AppID</th>
                        <th>Spiel</th>
                        <th>Status</th>
                        <th>Grund</th>
                        <th>Native</th>
                        <th>ProtonDB</th>
                        <th>Reports</th>
                        <th>Trending</th>
                        <th>SteamOS</th>
                        <th>Anti-Cheat</th>
                        <th>Anti-Cheat Systeme</th>
                        <th>Installiert</th>
                    </tr>
                </thead>

                <tbody id="game-table">
                    {rows_html}
                </tbody>
            </table>
        </section>

        <div
            id="result-count"
            class="result-count"
        ></div>
    </main>

    <script>
        const searchInput =
            document.getElementById("search");

        const installedOnly =
            document.getElementById("installed-only");

        const filterButtons =
            Array.from(
                document.querySelectorAll(
                    ".filter-button"
                )
            );

        const rows =
            Array.from(
                document.querySelectorAll(
                    "#game-table tr"
                )
            );

        const resultCount =
            document.getElementById(
                "result-count"
            );

        let activeStatus = "All";

        function updateTable() {{
            const searchTerm =
                searchInput.value
                    .trim()
                    .toLowerCase();

            const installedFilter =
                installedOnly.checked;

            let visibleRows = 0;

            for (const row of rows) {{
                const rowText =
                    row.textContent.toLowerCase();

                const rowStatus =
                    row.dataset.status;

                const rowInstalled =
                    row.dataset.installed === "true";

                const matchesSearch =
                    !searchTerm
                    || rowText.includes(searchTerm);

                const matchesStatus =
                    activeStatus === "All"
                    || rowStatus === activeStatus;

                const matchesInstalled =
                    !installedFilter
                    || rowInstalled;

                const visible =
                    matchesSearch
                    && matchesStatus
                    && matchesInstalled;

                row.classList.toggle(
                    "hidden",
                    !visible
                );

                if (visible) {{
                    visibleRows += 1;
                }}
            }}

            resultCount.textContent =
                `${{visibleRows}} von ${{rows.length}} Spielen angezeigt`;
        }}

        searchInput.addEventListener(
            "input",
            updateTable
        );

        installedOnly.addEventListener(
            "change",
            updateTable
        );

        for (const button of filterButtons) {{
            button.addEventListener(
                "click",
                () => {{
                    activeStatus =
                        button.dataset.filter;

                    for (
                        const otherButton
                        of filterButtons
                    ) {{
                        otherButton.classList.remove(
                            "active"
                        );
                    }}

                    button.classList.add(
                        "active"
                    );

                    updateTable();
                }}
            );
        }}

        updateTable();
    </script>
</body>
</html>
"""

    HTML_REPORT_FILE.write_text(
        report,
        encoding="utf-8",
    )

    return HTML_REPORT_FILE