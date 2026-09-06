from src.steam_linux_check.steam_detector import (
    find_installed_apps,
    find_steam_installation,
    find_steam_libraries,
    find_steam_user_id,
)
from steam_linux_check.providers.steam import get_owned_games
from steam_linux_check.providers.steam_store import get_app_details


def main() -> None:
    # Lokale Steam-Installation finden
    steam_path = find_steam_installation()

    if steam_path is None:
        print("Steam-Installation wurde nicht gefunden.")
        return

    print(f"Steam gefunden: {steam_path}")

    # SteamID64 ermitteln
    steam_id = find_steam_user_id(steam_path)

    if steam_id is None:
        print("SteamID64 wurde nicht gefunden.")
        return

    print(f"SteamID64: {steam_id}")

    # Gesamte Besitzbibliothek über Steam Web API abrufen
    owned_games = get_owned_games(steam_id)

    print(f"\nBesessene Steam-Spiele: {len(owned_games)}")

    # Steam-Store-Metadaten abrufen bzw. aus Cache laden
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

    print()
    print(f"Steam-Store-Daten erhalten: {len(store_infos)}")
    print(f"Native Linux-Spiele: {len(native_games)}")

    # Lokale Steam-Bibliotheken erkennen
    libraries = find_steam_libraries(steam_path)

    print("\nSteam-Bibliotheken:")

    for library in libraries:
        print(f"  - {library}")

    # Lokal installierte Steam-Apps erkennen
    apps = find_installed_apps(libraries)

    print(f"\nInstallierte Steam-Apps: {len(apps)}")

    for app in sorted(apps, key=lambda app: app.name.lower()):
        print(f"  {app.app_id:<10} {app.name}")


if __name__ == "__main__":
    main()