from dataclasses import dataclass
from pathlib import Path


@dataclass
class InstalledApp:
    app_id: int
    name: str
    library_path: Path

@dataclass
class OwnedGame:
    app_id: int
    name: str

@dataclass
class SteamStoreInfo:
    app_id: int
    name: str
    app_type: str
    windows: bool
    mac: bool
    linux: bool