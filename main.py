from __future__ import annotations

import sys

from app.config import AppConfig
from app.database import Database


def main() -> int:
    config = AppConfig.load()

    import shutil
    from app.config import DATA_DIR
    external_sound = DATA_DIR / "lingsheng.wav"
    if not external_sound.exists():
        internal_sound = config.project_root / "app" / "assets" / "sounds" / "lingsheng.wav"
        if internal_sound.exists():
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            shutil.copy2(internal_sound, external_sound)

    database = Database(config.database_path)
    database.initialize()
    database.seed_defaults()

    try:
        from PySide6.QtWidgets import QApplication
    except ModuleNotFoundError:
        print("PySide6 is not installed. Run: pip install -r requirements.txt")
        return 1

    from app.ui.main_window import MainWindow

    qt_app = QApplication(sys.argv)
    window = MainWindow(config=config, database=database)

    if config.start_fullscreen:
        window.showFullScreen()
    else:
        window.resize(1280, 800)
        window.showFullScreen()

    return qt_app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

