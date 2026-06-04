from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.services.reward_service import RewardService


class RewardStoreDialog(QDialog):
    store_updated = Signal()

    def __init__(self, reward_service: RewardService, parent=None) -> None:
        super().__init__(parent)
        self.reward_service = reward_service
        self.setWindowTitle("兑换商城")
        self.setMinimumSize(900, 600)
        self.setObjectName("parentSettingsDialog")  # Reuse the background style

        root = QVBoxLayout(self)
        root.setContentsMargins(32, 32, 32, 32)
        root.setSpacing(24)

        header = QHBoxLayout()
        title = QLabel("🎁 星星兑换商城")
        title.setObjectName("dialogTitle")
        
        self.balance_label = QLabel()
        self.balance_label.setObjectName("starsLabel")
        self._update_balance_label()

        close_button = QPushButton("关闭")
        close_button.setObjectName("actionButton")
        close_button.clicked.connect(self.accept)

        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self.balance_label)
        header.addWidget(close_button)
        root.addLayout(header)

        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(24)
        
        wrap = QWidget()
        wrap.setObjectName("transparentPane")
        wrap.setLayout(self.grid_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(wrap)
        root.addWidget(scroll, 1)

        self._reload_items()

    def _update_balance_label(self) -> None:
        stars = self.reward_service.total_stars()
        self.balance_label.setText(f"当前余额: ⭐ {stars}")

    def _reload_items(self) -> None:
        # Clear existing items
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()

        items = self.reward_service.list_active_store_items()
        current_stars = self.reward_service.total_stars()
        
        if not items:
            empty_lbl = QLabel("商城里还没有商品哦，请家长在后台添加~")
            empty_lbl.setStyleSheet("font-size: 24px; color: #17345c;")
            self.grid_layout.addWidget(empty_lbl, 0, 0, Qt.AlignCenter)
            return

        columns = 3
        for idx, item in enumerate(items):
            card = self._build_item_card(item, current_stars)
            card.setFixedSize(220, 260)
            self.grid_layout.addWidget(card, idx // columns, idx % columns)

        row_count = (len(items) - 1) // columns + 1
        self.grid_layout.setRowStretch(row_count, 1)
        self.grid_layout.setColumnStretch(columns, 1)

    def _build_item_card(self, item: dict, current_stars: int) -> QWidget:
        card = QFrame()
        card.setObjectName("storeCard")
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        icon = QLabel(item["icon"])
        icon.setObjectName("storeIcon")
        icon.setAlignment(Qt.AlignCenter)
        
        title = QLabel(item["title"])
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #ffffff;")
        title.setWordWrap(True)
        
        cost = item["cost_stars"]
        
        btn = QPushButton(f"兑换 ({cost} 星)")
        if current_stars >= cost:
            btn.setObjectName("storeRedeemButton")
            btn.clicked.connect(lambda checked=False, i_id=item["id"]: self._redeem(i_id))
        else:
            btn.setObjectName("storeDisabledButton")
            btn.setEnabled(False)
            btn.setText("星星不足")
            
        layout.addWidget(icon)
        layout.addWidget(title)
        layout.addStretch(1)
        layout.addWidget(btn)
        
        return card

    def _redeem(self, item_id: int) -> None:
        # Get the item details to show in success message
        item = next((it for it in self.reward_service.list_active_store_items() if it["id"] == item_id), None)
        if not item:
            return

        reply = QMessageBox.question(
            self, 
            "确认兑换", 
            f"确定要花费 {item['cost_stars']} 颗星星兑换【{item['title']}】吗？"
        )
        
        if reply == QMessageBox.Yes:
            success = self.reward_service.redeem_item(item_id)
            if success:
                QMessageBox.information(self, "兑换成功", f"恭喜你，成功兑换了【{item['title']}】！快去找家长吧~")
                self._update_balance_label()
                self._reload_items()
                self.store_updated.emit()
            else:
                QMessageBox.warning(self, "兑换失败", "哎呀，星星好像不够了。")
