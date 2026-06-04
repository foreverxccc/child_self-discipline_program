from __future__ import annotations

from PySide6.QtWidgets import QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from app.services.task_service import TaskService


class TaskPickerDialog(QDialog):
    def __init__(self, task_service: TaskService, icon_resolver, parent=None) -> None:
        super().__init__(parent)
        self.task_service = task_service
        self.icon_resolver = icon_resolver
        self.selected_template_id: int | None = None

        self.setWindowTitle("选择任务")
        self.resize(520, 620)
        self.setObjectName("taskPickerDialog")

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        title = QLabel("选择一个任务加入今天")
        title.setObjectName("dialogTitle")
        root.addWidget(title)

        self.template_list = QVBoxLayout()
        self.template_list.setSpacing(8)
        template_wrap = QWidget()
        template_wrap.setObjectName("transparentPane")
        template_wrap.setLayout(self.template_list)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(template_wrap)
        root.addWidget(scroll, 1)

        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        root.addWidget(cancel_button)

        self._reload_templates()

    def _reload_templates(self) -> None:
        for template in self.task_service.list_active_templates():
            row = QFrame()
            row.setObjectName("templateDialogItem")
            layout = QHBoxLayout(row)
            layout.setContentsMargins(12, 8, 12, 8)
            layout.setSpacing(10)

            icon = QLabel(self.icon_resolver(template["icon"]))
            icon.setObjectName("templateIcon")
            label = QLabel(template["title"])
            label.setObjectName("templateDialogTitle")
            add_button = QPushButton("加入")
            add_button.setObjectName("addPlanButton")
            add_button.clicked.connect(
                lambda checked=False, template_id=template["id"]: self._select_template(template_id)
            )

            layout.addWidget(icon)
            layout.addWidget(label, 1)
            layout.addWidget(add_button)
            self.template_list.addWidget(row)
        self.template_list.addStretch(1)

    def _select_template(self, template_id: int) -> None:
        self.selected_template_id = template_id
        self.accept()

