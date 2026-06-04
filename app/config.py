from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

if getattr(sys, 'frozen', False):
    # Running in a PyInstaller bundle
    PROJECT_ROOT = Path(sys._MEIPASS)
    # Store database next to the executable
    DATA_DIR = Path(sys.executable).parent / "data"
else:
    # Running in normal Python environment
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    DATA_DIR = PROJECT_ROOT / "data"

@dataclass(frozen=True)
class AppConfig:
    project_root: Path
    database_path: Path
    stylesheet_path: Path
    start_fullscreen: bool = False
    always_on_top: bool = False

    @classmethod
    def load(cls) -> "AppConfig":
        return cls(
            project_root=PROJECT_ROOT,
            database_path=DATA_DIR / "app.db",
            stylesheet_path=PROJECT_ROOT / "app" / "assets" / "styles.qss",
        )

