from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QInputDialog,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.services.task_service import TaskService
from app.services.auth_service import AuthService
from app.services.reward_service import RewardService


class ParentSettingsDialog(QDialog):
    settings_changed = Signal()

    CATEGORIES = [
        ("学习", "study"),
        ("生活", "life"),
        ("运动", "sport"),
        ("休息", "rest"),
        ("自定义", "custom"),
    ]

    ICONS = [
        ("书", "book"),
        ("笔", "pen"),
        ("算", "calculator"),
        ("诗", "scroll"),
        ("包", "bag"),
        ("家", "home"),
        ("洗", "smile"),
        ("跑", "activity"),
        ("伸", "person-standing"),
        ("水", "cup"),
        ("星", "star"),
    ]

    def __init__(self, task_service: TaskService, auth_service: AuthService, reward_service: RewardService, parent=None) -> None:
        super().__init__(parent)
        self.task_service = task_service
        self.auth_service = auth_service
        self.reward_service = reward_service
        self.current_store_id: int | None = None
        self.current_template_id: int | None = None
        self.setWindowTitle("家长设置")
        self.resize(1440, 960)
        self.setMinimumSize(1200, 800)
        self.setObjectName("parentSettingsDialog")

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        header = QHBoxLayout()
        title = QLabel("家长设置")
        title.setObjectName("dialogTitle")
        
        change_pwd_button = QPushButton("修改密码")
        change_pwd_button.setObjectName("actionButton")
        change_pwd_button.clicked.connect(self._change_password)
        
        close_button = QPushButton("完成")
        close_button.clicked.connect(self.accept)
        
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(change_pwd_button)
        header.addWidget(close_button)
        root.addLayout(header)

        self.tabs = QTabWidget()
        
        # Tab 1: Tasks
        tasks_tab = QWidget()
        tasks_layout = QHBoxLayout(tasks_tab)
        tasks_layout.setContentsMargins(0, 16, 0, 0)
        tasks_layout.setSpacing(14)
        tasks_layout.addWidget(self._build_template_list_panel(), 3)
        tasks_layout.addWidget(self._build_editor_panel(), 2)
        self.tabs.addTab(tasks_tab, "任务管理")
        
        # Tab 2: Store
        store_tab = QWidget()
        store_layout = QHBoxLayout(store_tab)
        store_layout.setContentsMargins(0, 16, 0, 0)
        store_layout.setSpacing(14)
        store_layout.addWidget(self._build_store_list_panel(), 3)
        store_layout.addWidget(self._build_store_editor_panel(), 2)
        self.tabs.addTab(store_tab, "商城管理")
        
        root.addWidget(self.tabs, 1)

        self._reload_templates()
        self._reset_form()
        self._reload_store_items()
        self._reset_store_form()

    def _build_template_list_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("settingsPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        heading = QLabel("任务模板")
        heading.setObjectName("sectionTitle")
        layout.addWidget(heading)

        self.template_list = QVBoxLayout()
        self.template_list.setSpacing(8)
        wrap = QWidget()
        wrap.setObjectName("transparentPane")
        wrap.setLayout(self.template_list)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(wrap)
        layout.addWidget(scroll, 1)
        return panel

    def _build_editor_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("settingsPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        heading = QLabel("编辑任务")
        heading.setObjectName("sectionTitle")
        layout.addWidget(heading)

        form = QGridLayout()
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(12)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("例如：阅读20分钟")

        self.icon_combo = QComboBox()
        for text, value in self.ICONS:
            self.icon_combo.addItem(text, value)

        self.category_combo = QComboBox()
        for text, value in self.CATEGORIES:
            self.category_combo.addItem(text, value)

        self.minutes_input = QSpinBox()
        self.minutes_input.setRange(1, 120)
        self.minutes_input.setValue(20)
        self.minutes_input.setSuffix(" 分钟")

        self.reward_input = QSpinBox()
        self.reward_input.setRange(0, 20)
        self.reward_input.setValue(1)
        self.reward_input.setSuffix(" 星")

        self.active_checkbox = QCheckBox("在孩子选择任务时显示")
        self.active_checkbox.setChecked(True)

        for row_idx, (text, widget) in enumerate([
            ("任务名称", self.title_input),
            ("图标", self.icon_combo),
            ("分类", self.category_combo),
            ("默认计时", self.minutes_input),
            ("完成奖励", self.reward_input),
        ]):
            lbl = QLabel(text)
            lbl.setObjectName("formLabel")
            form.addWidget(lbl, row_idx, 0)
            form.addWidget(widget, row_idx, 1)
        form.addWidget(self.active_checkbox, 5, 1)
        layout.addLayout(form)

        actions = QHBoxLayout()
        save_button = QPushButton("保存任务")
        save_button.setObjectName("primaryActionButton")
        save_button.clicked.connect(self._save_template)
        
        cancel_button = QPushButton("取消 / 新增")
        cancel_button.setObjectName("actionButton")
        cancel_button.clicked.connect(self._reset_form)
        
        actions.addWidget(save_button)
        actions.addWidget(cancel_button)
        layout.addLayout(actions)

        self.form_hint = QLabel("任务名称可以直接写成“阅读20分钟”，默认计时只用于点击任务时带入左侧计时器。")
        self.form_hint.setObjectName("hintText")
        self.form_hint.setWordWrap(True)
        layout.addWidget(self.form_hint)
        layout.addStretch(1)
        return panel

    def _reload_templates(self) -> None:
        self._clear_layout(self.template_list)
        for template in self.task_service.list_templates():
            row = QFrame()
            row.setObjectName("settingsTemplateItem")
            layout = QHBoxLayout(row)
            layout.setContentsMargins(10, 8, 10, 8)
            layout.setSpacing(8)

            icon = QLabel(self._icon_text(template["icon"]))
            icon.setObjectName("templateIcon")
            title = QLabel(template["title"])
            title.setObjectName("settingsTemplateTitle")
            state = QLabel("显示" if template["is_active"] else "隐藏")
            state.setObjectName("planStatus")

            edit_button = QPushButton("编辑")
            edit_button.clicked.connect(lambda checked=False, item=template: self._load_template(item))
            up_button = QPushButton("↑")
            up_button.setObjectName("moveButton")
            up_button.clicked.connect(lambda checked=False, item_id=template["id"]: self._move_template(item_id, -1))
            down_button = QPushButton("↓")
            down_button.setObjectName("moveButton")
            down_button.clicked.connect(lambda checked=False, item_id=template["id"]: self._move_template(item_id, 1))
            active_button = QPushButton("隐藏" if template["is_active"] else "显示")
            active_button.clicked.connect(
                lambda checked=False, item_id=template["id"], active=template["is_active"]: self._toggle_template(
                    item_id, not bool(active)
                )
            )
            delete_button = QPushButton("删除")
            delete_button.setObjectName("deleteButton")
            delete_button.clicked.connect(
                lambda checked=False, item_id=template["id"], item_title=template["title"]: self._delete_template(
                    item_id, item_title
                )
            )

            layout.addWidget(icon)
            layout.addWidget(title, 1)
            layout.addWidget(state)
            layout.addWidget(up_button)
            layout.addWidget(down_button)
            layout.addWidget(edit_button)
            layout.addWidget(active_button)
            layout.addWidget(delete_button)
            self.template_list.addWidget(row)
        self.template_list.addStretch(1)

    def _reset_form(self) -> None:
        self.current_template_id = None
        self.title_input.clear()
        self.icon_combo.setCurrentIndex(0)
        self.category_combo.setCurrentIndex(0)
        self.minutes_input.setValue(20)
        self.reward_input.setValue(1)
        self.active_checkbox.setChecked(True)
        self.form_hint.setText("任务名称可以直接写成“阅读20分钟”，默认计时只用于点击任务时带入左侧计时器。")
        
    def _change_password(self) -> None:
        new_pwd, ok = QInputDialog.getText(
            self,
            "修改家长密码",
            "请输入新的家长密码（建议使用数字组合）:",
            QLineEdit.EchoMode.Password,
        )
        if ok and new_pwd.strip():
            self.auth_service.change_parent_password(new_pwd.strip())
            QMessageBox.information(self, "成功", "家长密码已成功修改！")

    def _load_template(self, template: dict) -> None:
        self.current_template_id = template["id"]
        self.title_input.setText(template["title"])
        self._set_combo_value(self.icon_combo, template["icon"])
        self._set_combo_value(self.category_combo, template["category"])
        self.minutes_input.setValue(int(template["suggested_minutes"]))
        self.reward_input.setValue(int(template["reward_stars"]))
        self.active_checkbox.setChecked(bool(template["is_active"]))

    def _save_template(self) -> None:
        title = self.title_input.text().strip()
        if not title:
            self.form_hint.setText("请先填写任务名称。")
            return

        icon = str(self.icon_combo.currentData())
        category = str(self.category_combo.currentData())
        minutes = int(self.minutes_input.value())
        reward_stars = int(self.reward_input.value())

        if self.current_template_id is None:
            template_id = self.task_service.create_template(title, icon, category, minutes, reward_stars)
            self.current_template_id = template_id
        else:
            self.task_service.update_template(
                self.current_template_id,
                title,
                icon,
                category,
                minutes,
                reward_stars,
            )

        self.task_service.set_template_active(self.current_template_id, self.active_checkbox.isChecked())
        self.settings_changed.emit()
        self._reload_templates()
        self._reset_form()

    def _move_template(self, template_id: int, direction: int) -> None:
        self.task_service.move_template(template_id, direction)
        self.settings_changed.emit()
        self._reload_templates()

    def _toggle_template(self, template_id: int, is_active: bool) -> None:
        self.task_service.set_template_active(template_id, is_active)
        self.settings_changed.emit()
        self._reload_templates()

    def _delete_template(self, template_id: int, title: str) -> None:
        reply = QMessageBox.question(
            self,
            "\u786e\u8ba4\u5220\u9664",
            f"\u786e\u5b9a\u8981\u5220\u9664\u4efb\u52a1 \u201c{title}\u201d \u5417\uff1f\n\u5220\u9664\u540e\u4e0d\u53ef\u6062\u590d\u3002",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.task_service.delete_template(template_id)
            if self.current_template_id == template_id:
                self._reset_form()
            self.settings_changed.emit()
            self._reload_templates()

    @staticmethod
    def _set_combo_value(combo: QComboBox, value: str) -> None:
        index = combo.findData(value)
        if index >= 0:
            combo.setCurrentIndex(index)

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
            "star": "星",
        }
        return icons.get(icon, "星")

    @staticmethod
    def _clear_layout(layout: QVBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    # --- Store Management ---
    
    def _build_store_list_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("settingsPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        heading = QLabel("商城商品")
        heading.setObjectName("sectionTitle")
        layout.addWidget(heading)

        self.store_list = QVBoxLayout()
        self.store_list.setSpacing(8)
        wrap = QWidget()
        wrap.setObjectName("transparentPane")
        wrap.setLayout(self.store_list)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(wrap)
        layout.addWidget(scroll, 1)
        return panel

    def _build_store_editor_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("settingsPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        heading = QLabel("编辑商品")
        heading.setObjectName("sectionTitle")
        layout.addWidget(heading)

        form = QGridLayout()
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(12)

        self.store_title_input = QLineEdit()
        self.store_title_input.setPlaceholderText("例如：看动画片30分钟")

        self.store_cost_input = QSpinBox()
        self.store_cost_input.setRange(1, 1000)
        self.store_cost_input.setSuffix(" 星")

        self.store_active_checkbox = QCheckBox("在孩子商城中显示")

        form.addWidget(QLabel("商品名称"), 0, 0)
        form.addWidget(self.store_title_input, 0, 1)
        form.addWidget(QLabel("兑换价格"), 1, 0)
        form.addWidget(self.store_cost_input, 1, 1)
        form.addWidget(self.store_active_checkbox, 2, 1)

        layout.addLayout(form)
        layout.addStretch(1)

        actions = QHBoxLayout()
        save_button = QPushButton("保存商品")
        save_button.setObjectName("primaryActionButton")
        save_button.clicked.connect(self._save_store_item)
        
        cancel_button = QPushButton("取消")
        cancel_button.setObjectName("actionButton")
        cancel_button.clicked.connect(self._reset_store_form)
        
        actions.addWidget(save_button)
        actions.addWidget(cancel_button)
        layout.addLayout(actions)

        return panel

    def _reload_store_items(self) -> None:
        while self.store_list.count():
            item = self.store_list.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        items = self.reward_service.list_store_items()
        for idx, item in enumerate(items):
            row = QFrame()
            row.setObjectName("planItem")
            if item["is_active"] == 0:
                row.setStyleSheet("#planItem { background: #d0e3ff; }")

            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(12, 8, 12, 8)

            icon_lbl = QLabel(item["icon"])
            icon_lbl.setObjectName("planIcon")
            title_lbl = QLabel(item["title"])
            title_lbl.setStyleSheet("font-size: 20px; font-weight: 800; color: #ffffff;")
            if item["is_active"] == 0:
                title_lbl.setStyleSheet("font-size: 20px; font-weight: 800; color: #84a5d4;")
            
            cost_lbl = QLabel(f"{item['cost_stars']} 星")
            cost_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: #ffeb3b;")

            up_btn = QPushButton("↑")
            up_btn.setObjectName("actionButton")
            up_btn.clicked.connect(
                lambda checked=False, i_id=item["id"]: self._move_store_item(i_id, -1)
            )

            down_btn = QPushButton("↓")
            down_btn.setObjectName("actionButton")
            down_btn.clicked.connect(
                lambda checked=False, i_id=item["id"]: self._move_store_item(i_id, 1)
            )

            edit_btn = QPushButton("编辑")
            edit_btn.setObjectName("actionButton")
            edit_btn.clicked.connect(
                lambda checked=False, it=item: self._edit_store_item(it)
            )

            toggle_btn = QPushButton("隐藏" if item["is_active"] == 1 else "显示")
            toggle_btn.setObjectName("actionButton")
            toggle_btn.clicked.connect(
                lambda checked=False, i_id=item["id"], act=item["is_active"]: self._toggle_store_item(i_id, act)
            )

            del_btn = QPushButton("删除")
            del_btn.setStyleSheet("background: #f44336;")
            del_btn.clicked.connect(
                lambda checked=False, i_id=item["id"], t=item["title"]: self._delete_store_item(i_id, t)
            )

            if idx == 0:
                up_btn.setEnabled(False)
            if idx == len(items) - 1:
                down_btn.setEnabled(False)

            row_layout.addWidget(icon_lbl)
            row_layout.addWidget(title_lbl)
            row_layout.addStretch(1)
            row_layout.addWidget(cost_lbl)
            row_layout.addWidget(toggle_btn)
            row_layout.addWidget(up_btn)
            row_layout.addWidget(down_btn)
            row_layout.addWidget(edit_btn)
            row_layout.addWidget(del_btn)

            self.store_list.addWidget(row)

        self.store_list.addStretch(1)

    def _reset_store_form(self) -> None:
        self.current_store_id = None
        self.store_title_input.clear()
        self.store_cost_input.setValue(10)
        self.store_active_checkbox.setChecked(True)

    def _edit_store_item(self, item: dict) -> None:
        self.current_store_id = item["id"]
        self.store_title_input.setText(item["title"])
        self.store_cost_input.setValue(int(item["cost_stars"]))
        self.store_active_checkbox.setChecked(item["is_active"] == 1)

    def _save_store_item(self) -> None:
        title = self.store_title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "错误", "商品名称不能为空")
            return

        icon = "🎁"  # Default generic icon for all store items
        cost = self.store_cost_input.value()
        is_active = self.store_active_checkbox.isChecked()

        if self.current_store_id is None:
            new_id = self.reward_service.create_store_item(title, icon, cost)
            self.reward_service.set_store_item_active(new_id, is_active)
        else:
            self.reward_service.update_store_item(self.current_store_id, title, icon, cost)
            self.reward_service.set_store_item_active(self.current_store_id, is_active)

        self._reload_store_items()
        self._reset_store_form()
        self.settings_changed.emit()

    def _delete_store_item(self, item_id: int, title: str) -> None:
        rep = QMessageBox.question(self, "确认删除", f"确定要删除商品 '{title}' 吗？")
        if rep == QMessageBox.Yes:
            self.reward_service.delete_store_item(item_id)
            self._reload_store_items()
            self._reset_store_form()
            self.settings_changed.emit()

    def _toggle_store_item(self, item_id: int, current_active: int) -> None:
        self.reward_service.set_store_item_active(item_id, not current_active)
        self._reload_store_items()
        self.settings_changed.emit()

    def _move_store_item(self, item_id: int, direction: int) -> None:
        self.reward_service.move_store_item(item_id, direction)
        self._reload_store_items()
        self.settings_changed.emit()
