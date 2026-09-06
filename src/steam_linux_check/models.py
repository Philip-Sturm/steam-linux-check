from dataclasses import dataclass
from pathlib import Path


@dataclass
class InstalledApp:
    app_id: int
    name: str
    library_path: Path