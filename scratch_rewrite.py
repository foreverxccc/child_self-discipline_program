import re

def rewrite():
    path = r"d:\pythonWork\child_self-discipline_program\app\ui\parent_settings.py"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update imports if needed
    if "QTabWidget" not in content:
        content = content.replace("QSpinBox,\n", "QSpinBox,\n    QTabWidget,\n")
    
    if "RewardService" not in content:
        content = content.replace("from app.services.auth_service import AuthService", "from app.services.auth_service import AuthService\nfrom app.services.reward_service import RewardService")

    # 2. Update __init__ signature
    content = content.replace(
        "def __init__(self, task_service: TaskService, auth_service: AuthService, parent=None) -> None:",
        "def __init__(self, task_service: TaskService, auth_service: AuthService, reward_service: RewardService, parent=None) -> None:"
    )
    content = content.replace("self.auth_service = auth_service\n", "self.auth_service = auth_service\n        self.reward_service = reward_service\n        self.current_store_id: int | None = None\n")
    
    # 3. Replace body layout with QTabWidget
    old_body = """        body = QHBoxLayout()
        body.setSpacing(14)
        body.addWidget(self._build_template_list_panel(), 3)
        body.addWidget(self._build_editor_panel(), 2)
        root.addLayout(body, 1)

        self._reload_templates()
        self._reset_form()"""
        
    new_body = """        self.tabs = QTabWidget()
        
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
        self._reset_store_form()"""
    
    content = content.replace(old_body, new_body)
    
    # 4. Append store methods at the end of the file
    store_methods = """
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

        self.store_icon_combo = QComboBox()
        for label, icon_id in self.ICONS:
            self.store_icon_combo.addItem(label, icon_id)

        self.store_cost_input = QSpinBox()
        self.store_cost_input.setRange(1, 1000)
        self.store_cost_input.setSuffix(" 星")

        self.store_active_checkbox = QCheckBox("在孩子商城中显示")

        form.addWidget(QLabel("商品名称"), 0, 0)
        form.addWidget(self.store_title_input, 0, 1)
        form.addWidget(QLabel("图标"), 1, 0)
        form.addWidget(self.store_icon_combo, 1, 1)
        form.addWidget(QLabel("兑换价格"), 2, 0)
        form.addWidget(self.store_cost_input, 2, 1)
        form.addWidget(self.store_active_checkbox, 3, 1)

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
        self.store_icon_combo.setCurrentIndex(0)
        self.store_cost_input.setValue(10)
        self.store_active_checkbox.setChecked(True)

    def _edit_store_item(self, item: dict) -> None:
        self.current_store_id = item["id"]
        self.store_title_input.setText(item["title"])
        self.store_cost_input.setValue(int(item["cost_stars"]))
        self.store_active_checkbox.setChecked(item["is_active"] == 1)
        
        idx = self.store_icon_combo.findData(item["icon"])
        if idx >= 0:
            self.store_icon_combo.setCurrentIndex(idx)

    def _save_store_item(self) -> None:
        title = self.store_title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "错误", "商品名称不能为空")
            return

        icon = self.store_icon_combo.currentData()
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
"""
    
    content += store_methods
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    rewrite()
