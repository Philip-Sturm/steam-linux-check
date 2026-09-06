import re
from pathlib import Path

from .models import InstalledApp


def find_steam_installation() -> Path | None:
    """Find the local Steam installation directory."""

    candidates = [
        Path.home() / ".local/share/Steam",
        Path.home() / ".steam/steam",
        Path.home() / ".steam/root",
        Path.home() / ".var/app/com.valvesoftware.Steam/data/Steam",
    ]

    for path in candidates:
        if path.is_dir():
            return path.resolve()

    return None


def find_steam_libraries(steam_path: Path) -> list[Path]:
    """Read Steam library paths from libraryfolders.vdf."""

    library_file = steam_path / "steamapps/libraryfolders.vdf"

    if not library_file.is_file():
        return []

    libraries: list[Path] = []

    content = library_file.read_text(encoding="utf-8")

    for match in re.finditer(r'"path"\s+"([^"]+)"', content):
        library_path = Path(match.group(1))

        if library_path.is_dir():
            libraries.append(library_path.resolve())

    return libraries

def find_installed_apps(libraries: list[Path]) -> list[InstalledApp]:
    """Find installed Steam games in all detected libraries."""

    games: list[InstalledApp] = []

    for library in libraries:
        steamapps_path = library / "steamapps"

        for manifest in steamapps_path.glob("appmanifest_*.acf"):
            content = manifest.read_text(encoding="utf-8")

            app_id_match = re.search(r'"appid"\s+"(\d+)"', content)
            name_match = re.search(r'"name"\s+"([^"]+)"', content)

            if app_id_match is None or name_match is None:
                continue

            games.append(
                InstalledApp(
                    app_id=int(app_id_match.group(1)),
                    name=name_match.group(1),
                    library_path=library,
                )
            )

    return games