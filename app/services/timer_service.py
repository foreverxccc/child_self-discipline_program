from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.database import Database


@dataclass
class TimerState:
    selected_minutes: int = 10
    remaining_seconds: int = 600
    running: bool = False
    session_id: int | None = None


class TimerService:
    def __init__(self, database: Database) -> None:
        self.database = database
        self.state = TimerState()

    def select_minutes(self, minutes: int) -> TimerState:
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

