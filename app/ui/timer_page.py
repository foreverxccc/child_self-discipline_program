from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtMultimedia import QSoundEffect
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout

from app.services.timer_service import TimerService
from app.ui.dial_widget import DialWidget
from app.config import DATA_DIR


class TimerPage(QFrame):
    QUICK_MINUTES = [5, 10, 15, 20, 30, 45, 60]

    def __init__(self, timer_service: TimerService) -> None:
        super().__init__()
        self.timer_service = timer_service
        self.setObjectName("timerPanel")

        self.qt_timer = QTimer(self)
        self.qt_timer.setInterval(1000)
        self.qt_timer.timeout.connect(self._tick)
        
        self.alarm_sound = QSoundEffect(self)
        sound_url = QUrl.fromLocalFile(str(DATA_DIR / "lingsheng.wav"))
        self.alarm_sound.setSource(sound_url)
        self.alarm_sound.setLoopCount(QSoundEffect.Infinite.value)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        heading = QLabel("自由计时器")
        heading.setObjectName("sectionTitle")
        layout.addWidget(heading)

        self.dial = DialWidget()
        self.dial.value_changed.connect(self._select_minutes)
        layout.addWidget(self.dial, 0, alignment=Qt.AlignCenter)

        self.time_label = QLabel()
        self.time_label.setObjectName("timeLabel")
        layout.addWidget(self.time_label)

        quick_grid = QGridLayout()
        quick_grid.setSpacing(8)
        self.quick_buttons = []
        for minutes in self.QUICK_MINUTES:
            button = QPushButton(f"{minutes}分")
            button.setObjectName("quickMinuteButton")
            button.clicked.connect(lambda checked=False, value=minutes: self._select_minutes(value))
            self.quick_buttons.append(button)
            index = self.QUICK_MINUTES.index(minutes)
            quick_grid.addWidget(button, index // 4, index % 4)
        layout.addLayout(quick_grid)

        action_row = QHBoxLayout()
        self.start_button = QPushButton("开始")
        self.pause_button = QPushButton("暂停")
        self.reset_button = QPushButton("重置")
        self.start_button.setObjectName("primaryActionButton")
        self.start_button.clicked.connect(self._start)
        self.pause_button.clicked.connect(self._pause)
        self.reset_button.clicked.connect(self._reset)
        action_row.addWidget(self.start_button)
        action_row.addWidget(self.pause_button)
        action_row.addWidget(self.reset_button)
        layout.addLayout(action_row)

        hint = QLabel("计时器只是工具，完成情况由孩子在右侧自己选择。")
        hint.setObjectName("hintText")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        layout.addStretch(1)

        self._select_minutes(self.timer_service.state.selected_minutes)

    def _select_minutes(self, minutes: int) -> None:
        if self.timer_service.state.running:
            return
        self.timer_service.select_minutes(minutes)
        self.dial.blockSignals(True)
        self.dial.set_minutes(self.timer_service.state.selected_minutes)
        self.dial.blockSignals(False)
        self._render()

    def select_minutes(self, minutes: int) -> None:
        self._select_minutes(minutes)

    def _start(self) -> None:
        self.timer_service.start()
        self.qt_timer.start()
        self._render()

    def _pause(self) -> None:
        self.timer_service.pause()
        self.qt_timer.stop()
        self._render()

    def _reset(self) -> None:
        self.timer_service.reset()
        self.qt_timer.stop()
        self._render()

    def _tick(self) -> None:
        state = self.timer_service.tick()
        if not state.running:
            self.qt_timer.stop()
            if state.remaining_seconds == 0:
                self._play_alarm_and_show_dialog()
        self._render()

    def _play_alarm_and_show_dialog(self) -> None:
        self.alarm_sound.play()
        
        msg = QMessageBox(self)
        msg.setWindowTitle("时间到！")
        msg.setText("设定的倒计时结束啦！")
        msg.setIcon(QMessageBox.Information)
        msg.exec()
        
        self.alarm_sound.stop()
        self._reset()

    def _render(self) -> None:
        state = self.timer_service.state
        remaining = state.remaining_seconds
        minutes, seconds = divmod(remaining, 60)
        self.time_label.setText(f"{minutes:02d}:{seconds:02d}")
        
        # Disable inputs when running
        is_running = state.running
        self.dial.setEnabled(not is_running)
        self.start_button.setEnabled(not is_running)
        for btn in self.quick_buttons:
            btn.setEnabled(not is_running)
            
        # If the timer is running, smoothly update the dial position
        if is_running:
            self.dial.blockSignals(True)
            self.dial.set_minutes(remaining / 60.0)
            self.dial.blockSignals(False)
