from dataclasses import dataclass
from enum import Enum
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

@dataclass
class ProtonDBInfo:
    app_id: int
    tier: str | None
    confidence: str | None
    total_reports: int
    best_reported_tier: str | None
    trending_tier: str | None

class CompatibilityStatus(str, Enum):
    NATIVE = "Native"
    WORKS = "Works"
    PARTIAL = "Partial"
    BROKEN = "Broken"
    UNKNOWN = "Unknown"


@dataclass
class CompatibilityResult:
    app_id: int
    name: str
    status: CompatibilityStatus
    reason: str

@dataclass
class AntiCheatInfo:
    name: str
    status: str
    anticheats: list[str]

@dataclass
class AntiCheatInfo:
    app_id: int | None
    name: str
    status: str
    anticheats: list[str]

@dataclass
class SteamDeckInfo:
    app_id: int
    deck_category: int | None
    steamos_category: int | None