from collections import Counter

from steam_linux_check.compatibility import evaluate_compatibility
from steam_linux_check.providers.anticheat import get_anticheat_games
from steam_linux_check.providers.protondb import get_protondb_info
from steam_linux_check.providers.steam import get_owned_games
from steam_linux_check.providers.steam_store import get_app_details
from steam_linux_check.steam_detector import (
    find_installed_apps,
    find_steam_installation,
    find_steam_libraries,
    find_steam_user_id,
)


def main() -> None:
    # Steam lokal finden
    steam_path = find_steam_installation()

    if steam_path is None:
        print("Steam-Installation wurde nicht gefunden.")
        return

    print(f"Steam gefunden: {steam_path}")

    # SteamID64 finden
    steam_id = find_steam_user_id(steam_path)

    if steam_id is None:
        print("SteamID64 wurde nicht gefunden.")
        return

    print(f"SteamID64: {steam_id}")

    # Gesamte Besitzbibliothek abrufen
    owned_games = get_owned_games(steam_id)

    print(f"\nBesessene Steam-Spiele: {len(owned_games)}")

    # Steam-Store-Metadaten abrufen
    print(f"\nSteam-Store-Daten werden geprüft: {len(owned_games)} Spiele")

    store_infos = []

    for index, game in enumerate(owned_games, start=1):
        print(
            f"[{index:>3}/{len(owned_games)}] "
            f"{game.name}"
        )

        details = get_app_details(game.app_id)

        if details is not None:
            store_infos.append(details)

    # Native Linux-Spiele bestimmen
    native_games = [
        game
        for game in store_infos
        if game.app_type == "game" and game.linux
    ]

    native_app_ids = {
        game.app_id
        for game in native_games
    }

    print()
    print(f"Steam-Store-Daten erhalten: {len(store_infos)}")
    print(f"Native Linux-Spiele: {len(native_games)}")

    # Fehlende Steam-Store-Einträge anzeigen
    store_app_ids = {
        info.app_id
        for info in store_infos
    }

    missing_store_games = [
        game
        for game in owned_games
        if game.app_id not in store_app_ids
    ]

    if missing_store_games:
        print(f"\nKeine Steam-Store-Daten: {len(missing_store_games)}")

        for game in sorted(
            missing_store_games,
            key=lambda game: game.name.lower(),
        ):
            print(f"  {game.app_id:<10} {game.name}")

    # ProtonDB nur für nicht-native Spiele abrufen
    print("\nProtonDB-Daten werden geprüft...")

    proton_targets = [
        game
        for game in owned_games
        if game.app_id not in native_app_ids
    ]

    proton_infos = []

    for index, game in enumerate(proton_targets, start=1):
        print(
            f"[{index:>3}/{len(proton_targets)}] "
            f"{game.name}"
        )

        info = get_protondb_info(game.app_id)

        if info is not None:
            proton_infos.append(info)

    print()
    print(f"ProtonDB-relevante Spiele: {len(proton_targets)}")
    print(f"ProtonDB-Daten erhalten: {len(proton_infos)}")

    # Anti-Cheat-Daten laden
    anticheat_games = get_anticheat_games()

    anticheat_by_app_id = {
        game.app_id: game
        for game in anticheat_games
        if game.app_id is not None
    }

    print(f"\nAnti-Cheat-Datensätze: {len(anticheat_games)}")

    # Provider-Daten nach AppID indizieren
    store_info_by_app = {
        info.app_id: info
        for info in store_infos
    }

    proton_info_by_app = {
        info.app_id: info
        for info in proton_infos
    }

    # Kompatibilität aller Spiele bewerten
    compatibility_results = []

    for game in owned_games:
        result = evaluate_compatibility(
            game=game,
            store_info=store_info_by_app.get(game.app_id),
            proton_info=proton_info_by_app.get(game.app_id),
            anticheat_info=anticheat_by_app_id.get(game.app_id),
        )

        compatibility_results.append(result)

    # Zusammenfassung
    status_counts = Counter(
        result.status.value
        for result in compatibility_results
    )

    print("\nCompatibility Summary:")

    for status in ["Native", "Works", "Partial", "Broken", "Unknown"]:
        print(f"  {status:<8} {status_counts[status]}")

    # Bekannte Testfälle
    print("\nTestfälle:")

    test_app_ids = {
        620,       # Portal 2
        2406770,   # Bodycam
        1867240,   # WARDOGS
        976730,    # Halo MCC
        578080,    # PUBG
        359550,    # Rainbow Six Siege
    }

    for result in compatibility_results:
        if result.app_id in test_app_ids:
            print(
                f"  {result.name:<35} "
                f"{result.status.value:<8} "
                f"{result.reason}"
            )

    # Lokale Steam-Bibliotheken
    libraries = find_steam_libraries(steam_path)

    print("\nSteam-Bibliotheken:")

    for library in libraries:
        print(f"  - {library}")

    # Lokal installierte Steam-Apps
    apps = find_installed_apps(libraries)

    print(f"\nInstallierte Steam-Apps: {len(apps)}")

    for app in sorted(apps, key=lambda app: app.name.lower()):
        print(f"  {app.app_id:<10} {app.name}")


if __name__ == "__main__":
    main()