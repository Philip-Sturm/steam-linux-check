from src.steam_linux_check.steam_detector import (
    find_installed_apps,
    find_steam_installation,
    find_steam_libraries,
    find_steam_user_id,
)
from steam_linux_check.providers.steam import get_owned_games
from steam_linux_check.providers.steam_store import get_app_details


def main() -> None:
    steam_path = find_steam_installation()

    if steam_path is None:
        print("Steam-Installation wurde nicht gefunden.")
        return

    print(f"Steam gefunden: {steam_path}")

    steam_id = find_steam_user_id(steam_path)

    if steam_id is None:
        print("SteamID64 wurde nicht gefunden.")
    else:
        print(f"SteamID64: {steam_id}")

    if steam_id is not None:
        owned_games = get_owned_games(steam_id)

        print(f"\nBesessene Steam-Spiele: {len(owned_games)}")

        for game in sorted(owned_games, key=lambda game: game.name.lower()):
            print(f"  {game.app_id:<10} {game.name}")

    libraries = find_steam_libraries(steam_path)

    print("\nSteam-Bibliotheken:")

    for library in libraries:
        print(f"  - {library}")

    apps = find_installed_apps(libraries)

    print(f"\nInstallierte Steam-Apps: {len(apps)}")

    for app in sorted(apps, key=lambda app: app.name.lower()):
        print(f"  {app.app_id:<10} {app.name}")

    print("\nSteam Store Tests:")

    for app_id in [620, 2406770, 1867240]:
        details = get_app_details(app_id)

        if details is None:
            print(f"{app_id}: keine Daten")
            continue

        print(
            f"{details.app_id:<10} "
            f"{details.name:<25} "
            f"Type={details.app_type:<8} "
            f"Linux={details.linux}"
        )


if __name__ == "__main__":
    main()