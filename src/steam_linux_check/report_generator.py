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


def write_json_report(entries: list[GameReportEntry]) -> Path:
    """Write the compatibility report as JSON."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "total_games": len(entries),
        "games": [
            asdict(entry)
            for entry in entries
        ],
    }

    JSON_REPORT_FILE.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return JSON_REPORT_FILE


def write_csv_report(entries: list[GameReportEntry]) -> Path:
    """Write the compatibility report as CSV."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

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
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for entry in entries:
            row = asdict(entry)

            row["anticheats"] = ", ".join(
                entry.anticheats
            )

            writer.writerow(row)

    return CSV_REPORT_FILE


def write_html_report(
    entries: list[GameReportEntry],
    changes: list[ReportChange] | None = None,
) -> Path:
    """Write the compatibility report as a modern HTML dashboard."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    status_counts = {
        status: sum(1 for entry in entries if entry.status == status)
        for status in [
            "Native",
            "Works",
            "Partial",
            "Broken",
            "Unknown",
        ]
    }

    installed_count = sum(
        1 for entry in entries if entry.installed
    )

    # ---------------------------------------------------------
    # Änderungen seit letzter Prüfung
    # ---------------------------------------------------------

    changes = changes or []

    if changes:
        change_items = []

        for change in changes:
            details = "".join(
                f"<li>{html.escape(detail)}</li>"
                for detail in change.details
            )

            status_change = ""

            if (
                change.old_status is not None
                and change.new_status is not None
                and change.old_status != change.new_status
            ):
                status_change = (
                    '<div class="change-status">'
                    f"{html.escape(change.old_status)} "
                    f"→ {html.escape(change.new_status)}"
                    "</div>"
                )

            change_items.append(
                f"""
                <div class="change-item">
                    <div class="change-name">
                        {html.escape(change.name)}
                    </div>

                    {status_change}

                    <ul>
                        {details}
                    </ul>
                </div>
                """
            )

        changes_html = "".join(change_items)

    else:
        changes_html = """
        <div class="no-changes">
            Keine Änderungen seit der letzten Prüfung.
        </div>
        """

    # ---------------------------------------------------------
    # Tabellenzeilen
    # ---------------------------------------------------------

    rows = []

    for entry in entries:
        anticheats = ", ".join(entry.anticheats)

        rows.append(
            f"""
            <tr
                data-status="{html.escape(entry.status)}"
                data-installed="{str(entry.installed).lower()}"
            >
                <td class="appid">{entry.app_id}</td>

                <td class="game-name">
                    {html.escape(entry.name)}
                </td>

                <td>
                    <span class="status status-{entry.status.lower()}">
                        {html.escape(entry.status)}
                    </span>
                </td>

                <td>
                    {html.escape(entry.reason)}
                </td>

                <td>
                    {"✓" if entry.native_linux else ""}
                </td>

                <td>
                    {html.escape(entry.protondb_tier or "—")}
                </td>

                <td>
                    {entry.protondb_reports or "—"}
                </td>

                <td>
                    {html.escape(entry.protondb_trending or "—")}
                </td>

                <td>
                    {html.escape(entry.steamos_status or "—")}
                </td>

                <td>
                    {html.escape(entry.anticheat_status or "—")}
                </td>

                <td>
                    {html.escape(anticheats or "—")}
                </td>

                <td>
                    {"✓" if entry.installed else ""}
                </td>
            </tr>
            """
        )

    # ---------------------------------------------------------
    # HTML
    # ---------------------------------------------------------

    html_content = f"""<!DOCTYPE html>
<html lang="de">

<head>
    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>Steam Linux Compatibility</title>

    <style>
        :root {{
            color-scheme: dark;

            --bg: #07111f;
            --bg-secondary: #0b1728;
            --panel: #101f33;
            --panel-hover: #142842;

            --border: #233b58;

            --text: #e8f0fa;
            --muted: #8da4bd;

            --blue: #3b82f6;
            --blue-light: #60a5fa;

            --green: #34d399;
            --yellow: #fbbf24;
            --red: #f87171;
            --gray: #94a3b8;
        }}

        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;

            background:
                radial-gradient(
                    circle at top,
                    #10284a 0%,
                    var(--bg) 40%
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
            max-width: 1800px;
            margin: 0 auto;
            padding: 32px;
        }}

        header {{
            margin-bottom: 28px;
        }}

        h1 {{
            margin: 0;
            font-size: 2rem;
            font-weight: 700;
        }}

        .subtitle {{
            margin-top: 8px;
            color: var(--muted);
        }}

        .cards {{
            display: grid;

            grid-template-columns:
                repeat(auto-fit, minmax(150px, 1fr));

            gap: 14px;
            margin-bottom: 24px;
        }}

        .card {{
            background: rgba(16, 31, 51, 0.92);

            border: 1px solid var(--border);
            border-radius: 14px;

            padding: 18px;
        }}

        .card-label {{
            color: var(--muted);
            font-size: 0.85rem;
        }}

        .card-value {{
            margin-top: 5px;

            font-size: 1.8rem;
            font-weight: 700;
        }}

        .changes-panel {{
            margin-bottom: 18px;

            background: var(--panel);

            border: 1px solid var(--border);
            border-radius: 14px;

            overflow: hidden;
        }}

        .changes-panel summary {{
            cursor: pointer;

            padding: 16px 18px;

            font-weight: 600;

            user-select: none;
        }}

        .changes-panel summary:hover {{
            background: var(--panel-hover);
        }}

        .change-count {{
            margin-left: 8px;

            color: var(--blue-light);

            font-weight: 700;
        }}

        .changes-content {{
            padding: 0 18px 16px;
        }}

        .change-item {{
            padding: 12px 0;

            border-top: 1px solid var(--border);
        }}

        .change-name {{
            font-weight: 700;
        }}

        .change-status {{
            margin-top: 5px;

            color: var(--blue-light);
        }}

        .change-item ul {{
            margin: 8px 0 0;

            padding-left: 20px;

            color: var(--muted);
        }}

        .no-changes {{
            padding-top: 12px;

            color: var(--muted);
        }}

        .controls {{
            display: flex;
            flex-wrap: wrap;

            gap: 12px;

            align-items: center;

            background: var(--panel);

            border: 1px solid var(--border);
            border-radius: 14px;

            padding: 16px;

            margin-bottom: 18px;
        }}

        input[type="text"] {{
            flex: 1;

            min-width: 250px;

            background: var(--bg-secondary);

            border: 1px solid var(--border);
            border-radius: 9px;

            color: var(--text);

            padding: 10px 14px;

            font-size: 0.95rem;

            outline: none;
        }}

        input[type="text"]:focus {{
            border-color: var(--blue);
        }}

        button {{
            background: #13263e;

            color: var(--text);

            border: 1px solid var(--border);
            border-radius: 8px;

            padding: 9px 14px;

            cursor: pointer;
        }}

        button:hover {{
            background: #193555;
        }}

        button.active {{
            background: var(--blue);

            border-color: var(--blue);
        }}

        .installed-filter {{
            display: flex;

            align-items: center;

            gap: 7px;

            color: var(--muted);

            user-select: none;
        }}

        .table-wrapper {{
            overflow: auto;

            border: 1px solid var(--border);
            border-radius: 14px;

            background: var(--panel);
        }}

        table {{
            width: 100%;

            border-collapse: collapse;

            font-size: 0.88rem;
        }}

        th {{
            position: sticky;

            top: 0;

            z-index: 2;

            background: #0d1b2d;

            color: #bcd0e6;

            text-align: left;

            white-space: nowrap;

            padding: 13px 12px;

            border-bottom: 1px solid var(--border);
        }}

        td {{
            padding: 11px 12px;

            border-bottom: 1px solid #172c45;

            vertical-align: middle;
        }}

        tbody tr:hover {{
            background: var(--panel-hover);
        }}

        .appid {{
            color: var(--muted);

            font-family: monospace;
        }}

        .game-name {{
            font-weight: 600;

            white-space: nowrap;
        }}

        .status {{
            display: inline-block;

            min-width: 76px;

            text-align: center;

            font-weight: 600;

            border-radius: 20px;

            padding: 5px 10px;
        }}

        .status-native {{
            color: #6ee7b7;

            background: rgba(52, 211, 153, 0.13);
        }}

        .status-works {{
            color: #86efac;

            background: rgba(34, 197, 94, 0.13);
        }}

        .status-partial {{
            color: #fde047;

            background: rgba(234, 179, 8, 0.13);
        }}

        .status-broken {{
            color: #fca5a5;

            background: rgba(239, 68, 68, 0.13);
        }}

        .status-unknown {{
            color: #cbd5e1;

            background: rgba(148, 163, 184, 0.13);
        }}

        @media (max-width: 800px) {{
            .container {{
                padding: 16px;
            }}

            h1 {{
                font-size: 1.5rem;
            }}
        }}
    </style>
</head>

<body>

<div class="container">

<header>
    <h1>Steam Linux Compatibility</h1>

    <div class="subtitle">
        Fedora Compatibility Report · {len(entries)} Steam-Spiele
    </div>
</header>

<div class="cards">

    <div class="card">
        <div class="card-label">
            Gesamt
        </div>

        <div class="card-value">
            {len(entries)}
        </div>
    </div>

    <div class="card">
        <div class="card-label">
            Native
        </div>

        <div class="card-value">
            {status_counts["Native"]}
        </div>
    </div>

    <div class="card">
        <div class="card-label">
            Works
        </div>

        <div class="card-value">
            {status_counts["Works"]}
        </div>
    </div>

    <div class="card">
        <div class="card-label">
            Partial
        </div>

        <div class="card-value">
            {status_counts["Partial"]}
        </div>
    </div>

    <div class="card">
        <div class="card-label">
            Broken
        </div>

        <div class="card-value">
            {status_counts["Broken"]}
        </div>
    </div>

    <div class="card">
        <div class="card-label">
            Unknown
        </div>

        <div class="card-value">
            {status_counts["Unknown"]}
        </div>
    </div>

    <div class="card">
        <div class="card-label">
            Installiert
        </div>

        <div class="card-value">
            {installed_count}
        </div>
    </div>

</div>

<details class="changes-panel" open>

    <summary>
        Änderungen seit letzter Prüfung

        <span class="change-count">
            {len(changes)}
        </span>
    </summary>

    <div class="changes-content">
        {changes_html}
    </div>

</details>

<div class="controls">

    <input
        id="search"
        type="text"
        placeholder="Spiel suchen..."
        oninput="applyFilters()"
    >

    <button
        class="status-button active"
        onclick="setStatusFilter('all', this)"
    >
        Alle
    </button>

    <button
        class="status-button"
        onclick="setStatusFilter('Native', this)"
    >
        Native
    </button>

    <button
        class="status-button"
        onclick="setStatusFilter('Works', this)"
    >
        Works
    </button>

    <button
        class="status-button"
        onclick="setStatusFilter('Partial', this)"
    >
        Partial
    </button>

    <button
        class="status-button"
        onclick="setStatusFilter('Broken', this)"
    >
        Broken
    </button>

    <button
        class="status-button"
        onclick="setStatusFilter('Unknown', this)"
    >
        Unknown
    </button>

    <label class="installed-filter">

        <input
            id="installedOnly"
            type="checkbox"
            onchange="applyFilters()"
        >

        Nur installiert

    </label>

</div>

<div class="table-wrapper">

<table id="games">

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

<tbody>
{"".join(rows)}
</tbody>

</table>

</div>

</div>

<script>

let statusFilter = "all";


function setStatusFilter(status, button) {{

    statusFilter = status;

    document
        .querySelectorAll(".status-button")
        .forEach(element => {{
            element.classList.remove("active");
        }});

    button.classList.add("active");

    applyFilters();
}}


function applyFilters() {{

    const search = document
        .getElementById("search")
        .value
        .toLowerCase();

    const installedOnly = document
        .getElementById("installedOnly")
        .checked;

    const rows = document
        .querySelectorAll("#games tbody tr");

    rows.forEach(row => {{

        const name = row
            .children[1]
            .textContent
            .toLowerCase();

        const status = row.dataset.status;

        const installed =
            row.dataset.installed === "true";

        const matchesSearch =
            name.includes(search);

        const matchesStatus =
            statusFilter === "all" ||
            status === statusFilter;

        const matchesInstalled =
            !installedOnly ||
            installed;

        row.style.display =
            matchesSearch &&
            matchesStatus &&
            matchesInstalled
                ? ""
                : "none";
    }});
}}

</script>

</body>
</html>
"""

    HTML_REPORT_FILE.write_text(
        html_content,
        encoding="utf-8",
    )

    return HTML_REPORT_FILE