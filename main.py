from __future__ import annotations

import sys

from app.config import AppConfig
from app.database import Database


def main() -> int:
    # 1. 加载全局配置（自动判断是开发环境还是 PyInstaller 打包后的环境）
    config = AppConfig.load()

    # 2. 检查并复制默认提示音文件
    # 如果 data 目录下不存在 lingsheng.wav，则从内置的 assets 中提取一个过去，
    # 这样可以保证用户在打包的 exe 外部随时替换自己的提示音。
    import shutil
    from app.config import DATA_DIR
    external_sound = DATA_DIR / "lingsheng.wav"
    if not external_sound.exists():
        internal_sound = config.project_root / "app" / "assets" / "sounds" / "lingsheng.wav"
        if internal_sound.exists():
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            shutil.copy2(internal_sound, external_sound)

    # 3. 初始化 SQLite 数据库
    database = Database(config.database_path)
    database.initialize()
    database.seed_defaults()

    try:
        from PySide6.QtWidgets import QApplication
    except ModuleNotFoundError:
        print("PySide6 is not installed. Run: pip install -r requirements.txt")
        return 1

    from app.ui.main_window import MainWindow

    # 4. 启动 Qt 应用程序
    qt_app = QApplication(sys.argv)
    window = MainWindow(config=config, database=database)

    # 5. 默认全屏展示（防止孩子误触关闭），或者按 1280x800 分辨率展示
    if config.start_fullscreen:
        window.showFullScreen()
    else:
        window.resize(1280, 800)
        window.showFullScreen()

    return qt_app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

