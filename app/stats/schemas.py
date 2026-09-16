from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.habits.enums import Direction, HabitKind, PeriodScope
from app.stats.completeness import PeriodStatus


class HabitDayProgress(BaseModel):
    habit_id: int
    name: str
    kind: HabitKind
    period_scope: PeriodScope
    direction: Direction
    is_essential: bool
    today_total: Decimal
    target: Decimal
    cadence: int
    days_met: int
    status: PeriodStatus


class DaySummary(BaseModel):
    date: date
    essentials_met: bool
    habits_met: int
    habits_total: int
    habits: list[HabitDayProgress]


class HabitStats(BaseModel):
    habit_id: int
    name: str
    current_streak: int
    best_streak: int
    today: HabitDayProgress


class StreakSummary(BaseModel):
    habit_id: int
    name: str
    current_streak: int
    best_streak: int


class StreaksOverview(BaseModel):
    date: date
    streaks: list[StreakSummary]


class NeutralizedDayCreate(BaseModel):
    logical_date: date
    reason: str | None = None


class NeutralizedDayRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    logical_date: date
    reason: str | None
