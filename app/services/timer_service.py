from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.database import Database


@dataclass
class TimerState:
    """保存当前倒计时状态的数据结构"""
    selected_minutes: int = 10
    remaining_seconds: int = 600
    running: bool = False
    session_id: int | None = None


class TimerService:
    """
    负责处理番茄钟/倒计时的核心逻辑。
    包括开始计时、暂停、重置、每秒 tick 计算，以及将计时记录保存到数据库中。
    """
    def __init__(self, database: Database) -> None:
        self.database = database
        self.state = TimerState()

    def select_minutes(self, minutes: int) -> TimerState:
        """用户选择需要专注的分钟数（限制在1-120分钟内）"""
        safe_minutes = max(1, min(minutes, 120))
        self.state.selected_minutes = safe_minutes
        self.state.remaining_seconds = safe_minutes * 60
        return self.state

    def start(self, linked_plan_item_id: int | None = None) -> TimerState:
        self.state.running = True
        self.state.session_id = self.database.execute(
            """
            INSERT INTO timer_sessions(selected_minutes, linked_plan_item_id)
            VALUES (?, ?)
            """,
            (self.state.selected_minutes, linked_plan_item_id),
        )
        return self.state

    def pause(self) -> TimerState:
        self.state.running = False
        return self.state

    def reset(self) -> TimerState:
        self.state.running = False
        self.state.remaining_seconds = self.state.selected_minutes * 60
        return self.state

    def tick(self) -> TimerState:
        """时钟每秒滴答一次，更新剩余秒数。如果归零则触发完成事件"""
        if not self.state.running:
            return self.state

        self.state.remaining_seconds = max(0, self.state.remaining_seconds - 1)
        if self.state.remaining_seconds == 0:
            self.complete()
        return self.state

    def complete(self) -> TimerState:
        self.state.running = False
        if self.state.session_id is not None:
            actual_seconds = self.state.selected_minutes * 60 - self.state.remaining_seconds
            self.database.execute(
                """
                UPDATE timer_sessions
                SET actual_seconds = ?, ended_at = ?, status = 'completed'
                WHERE id = ?
                """,
                (actual_seconds, datetime.now().isoformat(timespec="seconds"), self.state.session_id),
            )
        return self.state

