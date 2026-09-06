from src.steam_linux_check.steam_detector import (
    find_installed_apps,
    find_steam_installation,
    find_steam_libraries,
)


def main() -> None:
    steam_path = find_steam_installation()

    if steam_path is None:
        print("Steam-Installation wurde nicht gefunden.")
        return

    print(f"Steam gefunden: {steam_path}")

    libraries = find_steam_libraries(steam_path)

    print("\nSteam-Bibliotheken:")

    for library in libraries:
        print(f"  - {library}")

    apps = find_installed_apps(libraries)

    print(f"\nInstallierte Steam-Apps: {len(apps)}")

    for app in sorted(apps, key=lambda app: app.name.lower()):
        print(f"  {app.app_id:<10} {app.name}")


if __name__ == "__main__":
    main()