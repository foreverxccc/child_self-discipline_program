from __future__ import annotations

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QLineEdit, QVBoxLayout

from app.services.auth_service import AuthService


class ParentLoginDialog(QDialog):
    def __init__(self, auth_service: AuthService, parent=None) -> None:
        super().__init__(parent)
        self.auth_service = auth_service
        self.setWindowTitle("家长验证")
        self.resize(600, 360)
        self.setMinimumSize(500, 300)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("请输入家长密码"))

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.returnPressed.connect(self._verify)
        layout.addWidget(self.password_input)

        self.error_label = QLabel("")
        self.error_label.setObjectName("errorText")
        layout.addWidget(self.error_label)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("确定")
        buttons.button(QDialogButtonBox.Cancel).setText("取消")
        buttons.accepted.connect(self._verify)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _verify(self) -> None:
        if self.auth_service.verify_parent_password(self.password_input.text()):
            self.accept()
        else:
            self.error_label.setText("密码不正确")

