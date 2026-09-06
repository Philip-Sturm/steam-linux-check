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
class GameReportEntry:
    app_id: int
    name: str
    status: str
    reason: str
    native_linux: bool
    protondb_tier: str | None
    protondb_confidence: str | None
    protondb_reports: int | None
    protondb_trending: str | None
    steamos_status: str | None
    anticheat_status: str | None
    anticheats: list[str]
    installed: bool


@dataclass
class ReportChange:
    app_id: int
    name: str
    change_type: str
    old_status: str | None
    new_status: str | None
    details: list[str]