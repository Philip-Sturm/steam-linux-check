from collections import Counter

from .analyzer import build_report_entries
from .data_collector import collect_compatibility_data
from .providers.steam import get_owned_games
from .report_generator import (
    write_csv_report,
    write_html_report,
    write_json_report,
)
from .state_manager import (
    compare_reports,
    load_previous_report,
    save_current_report,
)
from .steam_detector import (
    find_installed_apps,
    find_steam_installation,
    find_steam_libraries,
    find_steam_user_id,
)


def main() -> int:
    # ---------------------------------------------------------
    # Steam lokal erkennen
    # ---------------------------------------------------------

    steam_path = find_steam_installation()

    if steam_path is None:
        print("Steam-Installation wurde nicht gefunden.")
        return 1

    print(f"Steam gefunden: {steam_path}")

    steam_id = find_steam_user_id(steam_path)

    if steam_id is None:
        print("SteamID64 wurde nicht gefunden.")
        return 1

    print(f"SteamID64: {steam_id}")

    previous_report = load_previous_report()

    # ---------------------------------------------------------
    # Lokale Bibliotheken
    # ---------------------------------------------------------

    libraries = find_steam_libraries(steam_path)
    installed_apps = find_installed_apps(libraries)

    installed_app_ids = {
        app.app_id
        for app in installed_apps
    }

    print(f"\nSteam-Bibliotheken: {len(libraries)}")
    print(f"Installierte Steam-Apps: {len(installed_apps)}")

    # ---------------------------------------------------------
    # Besitzbibliothek
    # ---------------------------------------------------------

    try:
        owned_games = get_owned_games(steam_id)

    except (RuntimeError, TypeError) as error:
        print("\nSteam-Bibliothek konnte nicht geladen werden.")
        print(f"Grund: {error}")
        print("Der Check wird abgebrochen.")
        return 1

    print(f"Besessene Steam-Spiele: {len(owned_games)}")

    # ---------------------------------------------------------
    # Provider-Daten sammeln
    # ---------------------------------------------------------

    provider_data = collect_compatibility_data(
        owned_games
    )

    # ---------------------------------------------------------
    # Analyse
    # ---------------------------------------------------------

    compatibility_results, report_entries = build_report_entries(
        owned_games=owned_games,
        store_info_by_app=provider_data.store_info_by_app,
        proton_info_by_app=provider_data.proton_info_by_app,
        anticheat_by_app_id=provider_data.anticheat_by_app_id,
        deck_info_by_app=provider_data.deck_info_by_app,
        installed_app_ids=installed_app_ids,
    )

    # ---------------------------------------------------------
    # Zusammenfassung
    # ---------------------------------------------------------

    status_counts = Counter(
        result.status.value
        for result in compatibility_results
    )

    print("\nCompatibility Summary:")

    for status in [
        "Native",
        "Works",
        "Partial",
        "Broken",
        "Unknown",
    ]:
        print(
            f"  {status:<8} "
            f"{status_counts[status]}"
        )

    # ---------------------------------------------------------
    # Änderungen seit letztem Lauf
    # ---------------------------------------------------------

    changes = []

    if previous_report:
        changes = compare_reports(
            previous_report,
            report_entries,
        )

        print(
            f"\nÄnderungen seit letzter Prüfung: "
            f"{len(changes)}"
        )

        if not changes:
            print("  Keine Änderungen.")

        for change in changes:
            print(f"\n  {change.name}")

            if (
                change.old_status is not None
                and change.new_status is not None
                and change.old_status != change.new_status
            ):
                print(
                    f"    {change.old_status} "
                    f"→ {change.new_status}"
                )

            for detail in change.details:
                print(f"    {detail}")

    else:
        print(
            "\nKein vorheriger Zustand vorhanden. "
            "Baseline wird erstellt."
        )

    # ---------------------------------------------------------
    # Reports
    # ---------------------------------------------------------

    json_report_path = write_json_report(
        report_entries
    )

    csv_report_path = write_csv_report(
        report_entries
    )

    html_report_path = write_html_report(
        report_entries,
        changes=changes,
    )

    print("\nReports erstellt:")
    print(f"  JSON: {json_report_path}")
    print(f"  CSV:  {csv_report_path}")
    print(f"  HTML: {html_report_path}")

    # ---------------------------------------------------------
    # Zustand speichern
    # ---------------------------------------------------------

    save_current_report(
        report_entries
    )

    print("\nAktueller Zustand gespeichert.")

    return 0