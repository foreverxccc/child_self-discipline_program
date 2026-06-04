from __future__ import annotations

import datetime

from PySide6.QtCore import Signal, QTimer
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.services.plan_service import PlanService
from app.services.reward_service import RewardService
from app.services.task_service import TaskService
from app.services.timer_service import TimerService
from app.ui.task_picker_dialog import TaskPickerDialog
from app.ui.timer_page import TimerPage
from app.ui.toggle_switch import ToggleSwitch
from app.ui.reward_store_dialog import RewardStoreDialog


class ChildHomePage(QWidget):
    parent_requested = Signal()
    clear_requested = Signal()
    copy_requested = Signal()
    confirm_requested = Signal()
    unlock_requested = Signal()
    exit_requested = Signal()

    def __init__(
        self,
        task_service: TaskService,
        plan_service: PlanService,
        reward_service: RewardService,
        timer_service: TimerService,
    ) -> None:
        super().__init__()
        self.task_service = task_service
        self.plan_service = plan_service
        self.reward_service = reward_service
        self.timer_service = timer_service

        root = QVBoxLayout(self)
        root.setContentsMargins(48, 40, 48, 48)
        root.setSpacing(0)

        board = QFrame()
        board.setObjectName("devicePanel")
        board_layout = QVBoxLayout(board)
        board_layout.setContentsMargins(40, 32, 40, 40)
        board_layout.setSpacing(24)

        header = QHBoxLayout()
        title = QLabel("今天由我来安排")
        title.setObjectName("pageTitle")
        
        self.clock_label = QLabel()
        self.clock_label.setStyleSheet("font-size: 26px; color: #ffffff; font-weight: bold; margin-left: 24px; margin-top: 8px;")
        
        self.stars_label = QLabel()
        self.stars_label.setObjectName("starsLabel")
        
        store_button = QPushButton("兑换商城")
        store_button.setObjectName("actionButton")
        store_button.setStyleSheet("background: #ffc107; color: #8a5a00;")
        store_button.clicked.connect(self._open_store)
        
        parent_button = QPushButton("家长")
        parent_button.setObjectName("parentButton")
        parent_button.clicked.connect(self.parent_requested.emit)
        
        exit_button = QPushButton("退出")
        exit_button.setObjectName("actionButton")
        exit_button.clicked.connect(self.exit_requested.emit)

        header.addWidget(title)
        header.addWidget(self.clock_label)
        header.addStretch(1)
        header.addWidget(self.stars_label)
        header.addWidget(store_button)
        header.addWidget(parent_button)
        header.addWidget(exit_button)
        board_layout.addLayout(header)

        body = QHBoxLayout()
        body.setSpacing(18)
        self.timer_page = TimerPage(timer_service)
        body.addWidget(self.timer_page, 4)
        body.addWidget(self._build_plan_panel(), 5)
        board_layout.addLayout(body, 1)

        root.addWidget(board, 1)
        self.refresh()

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)
        self._update_clock()

    def _update_clock(self) -> None:
        now = datetime.datetime.now()
        weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        self.clock_label.setText(now.strftime("%Y年%m月%d日 {} %H:%M:%S").format(weekdays[now.weekday()]))

    def refresh(self) -> None:
        self.stars_label.setText(f"星星：{self.reward_service.total_stars()}")
        self._reload_plan_items()

    def _open_store(self) -> None:
        dialog = RewardStoreDialog(self.reward_service, self)
        dialog.store_updated.connect(self.refresh)
        dialog.exec()
        self.refresh()

    def _build_plan_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("planPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        heading = QLabel("今日计划")
        heading.setObjectName("sectionTitle")
        
        self.copy_button = QPushButton("复制昨天")
        self.copy_button.setObjectName("actionButton")
        self.copy_button.clicked.connect(self.copy_requested.emit)
        
        self.clear_button = QPushButton("清空")
        self.clear_button.setObjectName("actionButton")
        self.clear_button.clicked.connect(self.clear_requested.emit)
        
        self.add_button = QPushButton("+ 选择任务")
        self.add_button.setObjectName("chooseTaskButton")
        self.add_button.clicked.connect(self._open_task_picker)
        
        self.confirm_button = QPushButton("确认计划")
        self.confirm_button.setObjectName("primaryActionButton")
        self.confirm_button.clicked.connect(self.confirm_requested.emit)
        
        self.unlock_button = QPushButton("解锁计划")
        self.unlock_button.setObjectName("actionButton")
        self.unlock_button.clicked.connect(self.unlock_requested.emit)
        
        heading_row = QHBoxLayout()
        heading_row.addWidget(heading)
        heading_row.addStretch(1)
        heading_row.addWidget(self.copy_button)
        heading_row.addWidget(self.clear_button)
        heading_row.addWidget(self.add_button)
        heading_row.addWidget(self.confirm_button)
        heading_row.addWidget(self.unlock_button)
        layout.addLayout(heading_row)

        self.plan_list = QVBoxLayout()
        self.plan_list.setSpacing(16)
        plan_wrap = QWidget()
        plan_wrap.setObjectName("transparentPane")
        plan_wrap.setLayout(self.plan_list)

        plan_scroll = QScrollArea()
        plan_scroll.setWidgetResizable(True)
        plan_scroll.setWidget(plan_wrap)
        layout.addWidget(plan_scroll, 1)

        return panel

    def _reload_plan_items(self) -> None:
        self._clear_layout(self.plan_list)
        
        is_confirmed = self.plan_service.is_plan_confirmed()
        self.copy_button.setVisible(not is_confirmed)
        self.clear_button.setVisible(not is_confirmed)
        self.add_button.setVisible(not is_confirmed)
        self.confirm_button.setVisible(not is_confirmed)
        self.unlock_button.setVisible(is_confirmed)
        
        items = self.plan_service.list_today_items()
        if not items:
            empty = QLabel("今天还没有安排任务哦，点击右上角选择任务吧~")
            empty.setObjectName("emptyText")
            empty.setWordWrap(True)
            self.plan_list.addWidget(empty)
            return

        for item in items:
            row = QFrame()
            row.setObjectName("planItem")
            layout = QHBoxLayout(row)
            layout.setContentsMargins(12, 7, 10, 7)
            layout.setSpacing(8)

            icon = QLabel(self._icon_text(item["icon"]))
            icon.setObjectName("planIcon")
            label = QPushButton(item["title"])
            label.setObjectName("planLabelButton")
            label.clicked.connect(
                lambda checked=False, minutes=item["suggested_minutes"]: self._select_plan_minutes(minutes)
            )
            status = QLabel(self._status_text(item["status"]))
            status.setObjectName("planStatus")

            layout.addWidget(icon)
            layout.addWidget(label, 1)
            layout.addWidget(status)

            # The toggle switch replaces complete/fail buttons
            switch = ToggleSwitch(checked=(item["status"] == "completed"))
            switch.toggled.connect(lambda checked, item_id=item["id"]: self._toggle_item(item_id, checked))
            layout.addWidget(switch)

            if not is_confirmed:
                delete_button = QPushButton("🗑")
                delete_button.setObjectName("deleteButton")
                delete_button.clicked.connect(lambda checked=False, item_id=item["id"]: self._remove_item(item_id))
                layout.addWidget(delete_button)

            self.plan_list.addWidget(row)
        self.plan_list.addStretch(1)

    def _open_task_picker(self) -> None:
        dialog = TaskPickerDialog(self.task_service, self._icon_text, self)
        if dialog.exec() and dialog.selected_template_id is not None:
            self._add_template(dialog.selected_template_id)

    def _select_plan_minutes(self, minutes: int) -> None:
        self.timer_page.select_minutes(minutes)

    def _add_template(self, template_id: int) -> None:
        self.plan_service.add_template_to_today(template_id)
        self.refresh()

    def _toggle_item(self, item_id: int, checked: bool) -> None:
        if checked:
            self.plan_service.mark_completed(item_id)
            self.reward_service.grant_for_plan_item(item_id)
        else:
            self.plan_service.mark_pending(item_id)
            self.reward_service.revoke_for_plan_item(item_id)
            
        # Update stars immediately
        self.stars_label.setText(f"星星：{self.reward_service.total_stars()}")
        # Delay the full refresh so the toggle animation can finish smoothly
        QTimer.singleShot(250, self.refresh)

    def _remove_item(self, item_id: int) -> None:
        self.plan_service.remove_item(item_id)
        self.refresh()

    @staticmethod
    def _status_text(status: str) -> str:
        if status == "completed":
            return "已完成"
        if status == "failed":
            return "未完成"
        if status == "skipped":
            return "跳过"
        return "待完成"

    @staticmethod
    def _icon_text(icon: str) -> str:
        icons = {
            "book": "书",
            "pen": "笔",
            "calculator": "算",
            "scroll": "诗",
            "bag": "包",
            "home": "家",
            "smile": "洗",
            "activity": "跑",
            "person-standing": "伸",
            "cup": "水",
        }
        return icons.get(icon, "星")

    @staticmethod
    def _clear_layout(layout: QVBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
