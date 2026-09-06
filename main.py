from collections import Counter

from steam_linux_check.analyzer import build_report_entries
from steam_linux_check.providers.anticheat import get_anticheat_games
from steam_linux_check.providers.protondb import get_protondb_info
from steam_linux_check.providers.steam import get_owned_games
from steam_linux_check.providers.steam_deck import get_steam_deck_info
from steam_linux_check.providers.steam_store import get_app_details
from steam_linux_check.report_generator import (
    write_csv_report,
    write_html_report,
    write_json_report,
)
from steam_linux_check.state_manager import (
    compare_reports,
    load_previous_report,
    save_current_report,
)
from steam_linux_check.steam_detector import (
    find_installed_apps,
    find_steam_installation,
    find_steam_libraries,
    find_steam_user_id,
)


def main() -> None:
    # ---------------------------------------------------------
    # Steam lokal erkennen
    # ---------------------------------------------------------

    steam_path = find_steam_installation()

    if steam_path is None:
        print("Steam-Installation wurde nicht gefunden.")
        return

    print(f"Steam gefunden: {steam_path}")

    steam_id = find_steam_user_id(steam_path)

    if steam_id is None:
        print("SteamID64 wurde nicht gefunden.")
        return

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

    owned_games = get_owned_games(steam_id)

    print(f"Besessene Steam-Spiele: {len(owned_games)}")

    # ---------------------------------------------------------
    # Steam Store
    # ---------------------------------------------------------

    print(
        f"\nSteam-Store-Daten werden geprüft: "
        f"{len(owned_games)} Spiele"
    )

    store_infos = []

    for index, game in enumerate(owned_games, start=1):
        print(
            f"[{index:>3}/{len(owned_games)}] "
            f"{game.name}"
        )

        info = get_app_details(game.app_id)

        if info is not None:
            store_infos.append(info)

    store_info_by_app = {
        info.app_id: info
        for info in store_infos
    }

    native_app_ids = {
        info.app_id
        for info in store_infos
        if info.app_type == "game" and info.linux
    }

    print()
    print(f"Steam-Store-Daten erhalten: {len(store_infos)}")
    print(f"Native Linux-Spiele: {len(native_app_ids)}")

    # ---------------------------------------------------------
    # ProtonDB
    # ---------------------------------------------------------

    proton_targets = [
        game
        for game in owned_games
        if game.app_id not in native_app_ids
    ]

    print(
        f"\nProtonDB-Daten werden geprüft: "
        f"{len(proton_targets)} Spiele"
    )

    proton_infos = []

    for index, game in enumerate(proton_targets, start=1):
        print(
            f"[{index:>3}/{len(proton_targets)}] "
            f"{game.name}"
        )

        info = get_protondb_info(game.app_id)

        if info is not None:
            proton_infos.append(info)

    proton_info_by_app = {
        info.app_id: info
        for info in proton_infos
    }

    print()
    print(f"ProtonDB-Daten erhalten: {len(proton_infos)}")

    # ---------------------------------------------------------
    # Anti-Cheat
    # ---------------------------------------------------------

    anticheat_games = get_anticheat_games()

    anticheat_by_app_id = {
        game.app_id: game
        for game in anticheat_games
        if game.app_id is not None
    }

    print(
        f"\nAnti-Cheat-Datensätze: "
        f"{len(anticheat_games)}"
    )

    # ---------------------------------------------------------
    # Steam Deck / SteamOS
    # ---------------------------------------------------------

    deck_targets = [
        game
        for game in owned_games
        if game.app_id not in native_app_ids
    ]

    print(
        f"\nSteam-Deck-/SteamOS-Daten werden geprüft: "
        f"{len(deck_targets)} Spiele"
    )

    deck_infos = []

    for index, game in enumerate(deck_targets, start=1):
        print(
            f"[{index:>3}/{len(deck_targets)}] "
            f"{game.name}"
        )

        info = get_steam_deck_info(game.app_id)

        if info is not None:
            deck_infos.append(info)

    deck_info_by_app = {
        info.app_id: info
        for info in deck_infos
    }

    print()
    print(f"Steam-Deck-Daten erhalten: {len(deck_infos)}")

    # ---------------------------------------------------------
    # Analyse
    # ---------------------------------------------------------

    compatibility_results, report_entries = build_report_entries(
        owned_games=owned_games,
        store_info_by_app=store_info_by_app,
        proton_info_by_app=proton_info_by_app,
        anticheat_by_app_id=anticheat_by_app_id,
        deck_info_by_app=deck_info_by_app,
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

    json_report_path = write_json_report(report_entries)
    csv_report_path = write_csv_report(report_entries)

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

    save_current_report(report_entries)

    print("\nAktueller Zustand gespeichert.")


if __name__ == "__main__":
    main()