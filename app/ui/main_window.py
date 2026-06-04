from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QWidget
import keyboard

from app.config import AppConfig
from app.database import Database
from app.services.auth_service import AuthService
from app.services.plan_service import PlanService
from app.services.reward_service import RewardService
from app.services.task_service import TaskService
from app.services.timer_service import TimerService
from app.ui.child_home import ChildHomePage
from app.ui.parent_login import ParentLoginDialog
from app.ui.parent_settings import ParentSettingsDialog


class MainWindow(QMainWindow):
    def __init__(self, config: AppConfig, database: Database) -> None:
        super().__init__()
        self.config = config
        self.database = database
        self.auth_service = AuthService(database)
        self.task_service = TaskService(database)
        self.plan_service = PlanService(database)
        self.reward_service = RewardService(database)
        self.timer_service = TimerService(database)

        self.setWindowTitle("儿童自律计划")
        if config.always_on_top:
            self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
            
        try:
            keyboard.add_hotkey('alt+tab', lambda: None, suppress=True)
            keyboard.add_hotkey('windows', lambda: None, suppress=True)
            keyboard.add_hotkey('ctrl+esc', lambda: None, suppress=True)
            keyboard.add_hotkey('alt+esc', lambda: None, suppress=True)
        except Exception:
            pass

        self.home_page = ChildHomePage(
            task_service=self.task_service,
            plan_service=self.plan_service,
            reward_service=self.reward_service,
            timer_service=self.timer_service,
        )
        self.home_page.parent_requested.connect(self.open_parent_login)
        self.home_page.clear_requested.connect(self.handle_clear_requested)
        self.home_page.copy_requested.connect(self.handle_copy_requested)
        self.home_page.confirm_requested.connect(self.handle_confirm_requested)
        self.home_page.unlock_requested.connect(self.handle_unlock_requested)
        self.home_page.exit_requested.connect(self.close)

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.home_page)
        self.setCentralWidget(container)

        if config.stylesheet_path.exists():
            assets_dir = config.stylesheet_path.parent.as_posix()
            qss = config.stylesheet_path.read_text(encoding="utf-8")
            qss = qss.replace("{{ASSETS}}", assets_dir)
            self.setStyleSheet(qss)

    def open_parent_login(self) -> None:
        dialog = ParentLoginDialog(self.auth_service, self)
        if dialog.exec():
            settings_dialog = ParentSettingsDialog(self.task_service, self.auth_service, self.reward_service, self)
            settings_dialog.settings_changed.connect(self.home_page.refresh)
            settings_dialog.exec()
            self.home_page.refresh()

    def handle_clear_requested(self) -> None:
        dialog = ParentLoginDialog(self.auth_service, self)
        if dialog.exec():
            self.plan_service.clear_today_items()
            self.home_page.refresh()

    def handle_copy_requested(self) -> None:
        dialog = ParentLoginDialog(self.auth_service, self)
        if dialog.exec():
            self.plan_service.copy_yesterday_items()
            self.home_page.refresh()

    def handle_confirm_requested(self) -> None:
        # Kids can lock their plan without a password
        self.plan_service.set_plan_confirmed(True)
        self.home_page.refresh()

    def handle_unlock_requested(self) -> None:
        # Unlocking requires parent password
        dialog = ParentLoginDialog(self.auth_service, self)
        if dialog.exec():
            self.plan_service.set_plan_confirmed(False)
            self.home_page.refresh()

    def closeEvent(self, event) -> None:  # noqa: N802
        dialog = ParentLoginDialog(self.auth_service, self)
        if dialog.exec():
            event.accept()
        else:
            event.ignore()
