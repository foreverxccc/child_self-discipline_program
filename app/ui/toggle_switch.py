from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QRectF, Qt, Signal, Property
from PySide6.QtGui import QColor, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QWidget


class ToggleSwitch(QWidget):
    toggled = Signal(bool)

    def __init__(self, checked: bool = False, parent=None):
        super().__init__(parent)
        self.setFixedSize(80, 40)
        self._checked = checked
        self._position = 40 if checked else 0

        self.animation = QPropertyAnimation(self, b"position")
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.animation.setDuration(200)

    @Property(float)
    def position(self) -> float:
        return self._position

    @position.setter
    def position(self, pos: float) -> None:
        self._position = pos
        self.update()

    def is_checked(self) -> bool:
        return self._checked

    def set_checked(self, checked: bool) -> None:
        if self._checked == checked:
            return
        self._checked = checked
        self.animation.setEndValue(40 if checked else 0)
        self.animation.start()
        self.toggled.emit(checked)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton:
            self.set_checked(not self._checked)
        super().mouseReleaseEvent(event)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Background
        # Red when unchecked (0), Green when checked (40)
        # Interpolate color based on position
        progress = self._position / 40.0
        r = int(235 - (235 - 34) * progress)   # #eb4d4b (235, 77, 75) to #22c55e (34, 197, 94)
        g = int(77 + (197 - 77) * progress)
        b = int(75 + (94 - 75) * progress)
        bg_color = QColor(r, g, b)

        painter.setPen(Qt.NoPen)
        painter.setBrush(bg_color)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 20, 20)

        # Draw the circle
        circle_radius = 16
        circle_x = int(4 + self._position)
        circle_y = 4
        
        painter.setBrush(QColor("#ffffff"))
        painter.drawEllipse(circle_x, circle_y, circle_radius * 2, circle_radius * 2)

        # Draw Check/Cross inside the circle
        painter.setPen(QPen(bg_color, 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        if progress > 0.5:
            # Draw Check (✓)
            painter.drawLine(circle_x + 9, circle_y + 15, circle_x + 14, circle_y + 21)
            painter.drawLine(circle_x + 14, circle_y + 21, circle_x + 22, circle_y + 10)
        else:
            # Draw Cross (×)
            painter.drawLine(circle_x + 10, circle_y + 10, circle_x + 22, circle_y + 22)
            painter.drawLine(circle_x + 22, circle_y + 10, circle_x + 10, circle_y + 22)

        painter.end()
