from __future__ import annotations

import math

from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QMouseEvent, QPainter, QPen
from PySide6.QtWidgets import QWidget


class DialWidget(QWidget):
    value_changed = Signal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._minutes = 10
        self.setMinimumSize(360, 360)
        self.setCursor(Qt.PointingHandCursor)

    @property
    def minutes(self) -> float:
        return self._minutes

    def set_minutes(self, minutes: float) -> None:
        bounded = max(0.0, min(60.0, float(minutes)))
        if bounded == self._minutes:
            return
        self._minutes = bounded
        self.value_changed.emit(int(round(self._minutes)))
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self._update_from_position(event.position())

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self._update_from_position(event.position())

    def paintEvent(self, event) -> None:  # noqa: N802
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        side = min(self.width(), self.height())
        center = QPointF(self.width() / 2, self.height() / 2)
        radius = side * 0.42

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#f4fbff"))
        painter.drawEllipse(center, radius + 18, radius + 18)

        painter.setBrush(QColor("#2779e9"))
        start_angle = 90 * 16
        span_angle = -int(self._minutes / 60 * 360 * 16)
        painter.drawPie(
            int(center.x() - radius),
            int(center.y() - radius),
            int(radius * 2),
            int(radius * 2),
            start_angle,
            span_angle,
        )

        painter.setBrush(QColor("#e8f4ff"))
        painter.drawEllipse(center, radius * 0.62, radius * 0.62)

        for minute in range(0, 60):
            angle = math.radians(minute * 6 - 90)
            outer = radius + 8
            inner = radius - (16 if minute % 5 == 0 else 8)
            p1 = QPointF(center.x() + math.cos(angle) * inner, center.y() + math.sin(angle) * inner)
            p2 = QPointF(center.x() + math.cos(angle) * outer, center.y() + math.sin(angle) * outer)
            painter.setPen(QPen(QColor("#1f56a8"), 3 if minute % 5 == 0 else 1))
            painter.drawLine(p1, p2)

            if minute % 5 == 0:
                label_radius = radius + 31
                text_point = QPointF(
                    center.x() + math.cos(angle) * label_radius - 12,
                    center.y() + math.sin(angle) * label_radius + 7,
                )
                painter.setPen(QColor("#35618d"))
                painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
                painter.drawText(text_point, str(minute))

        handle_angle = math.radians(self._minutes * 6 - 90)
        handle_radius = radius * 0.84
        handle_center = QPointF(
            center.x() + math.cos(handle_angle) * handle_radius,
            center.y() + math.sin(handle_angle) * handle_radius,
        )
        painter.setPen(QPen(QColor("#ffffff"), 4))
        painter.setBrush(QColor("#1d66d6"))
        painter.drawEllipse(handle_center, 12, 12)

        painter.setPen(QPen(QColor("#5aa2ff"), 4))
        painter.setBrush(QColor("#d9ecff"))
        painter.drawEllipse(center, radius * 0.34, radius * 0.34)

        painter.setPen(QColor("#21549c"))
        painter.setFont(QFont("Microsoft YaHei", 18, QFont.Black))
        display_minutes = int(math.ceil(self._minutes))
        painter.drawText(
            int(center.x() - radius * 0.34),
            int(center.y() - radius * 0.16),
            int(radius * 0.68),
            int(radius * 0.28),
            Qt.AlignCenter,
            str(display_minutes),
        )
        painter.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
        painter.drawText(
            int(center.x() - radius * 0.34),
            int(center.y() + radius * 0.08),
            int(radius * 0.68),
            int(radius * 0.24),
            Qt.AlignCenter,
            "分钟",
        )

    def _update_from_position(self, position: QPointF) -> None:
        center = QPointF(self.width() / 2, self.height() / 2)
        dx = position.x() - center.x()
        dy = position.y() - center.y()
        degrees = (math.degrees(math.atan2(dy, dx)) + 90) % 360
        minutes = int(round(degrees / 6)) % 60
        self.set_minutes(60 if minutes == 0 and dy < 0 else minutes)

