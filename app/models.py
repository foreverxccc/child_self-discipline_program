from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum


class TaskCategory(StrEnum):
    STUDY = "study"
    LIFE = "life"
    SPORT = "sport"
    REST = "rest"
    CUSTOM = "custom"


class PlanStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TimerStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class TaskTemplate:
    id: int
    title: str
    icon: str
    category: TaskCategory
    suggested_minutes: int
    reward_stars: int
    sort_order: int
    is_active: bool


@dataclass(frozen=True)
class DailyPlanItem:
    id: int
    plan_date: date
    template_id: int
    title: str
    icon: str
    suggested_minutes: int
    reward_stars: int
    sort_order: int
    status: PlanStatus
    completed_at: datetime | None

