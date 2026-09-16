from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.habits.enums import Direction, HabitKind, PeriodScope


class HabitDayProgress(BaseModel):
    habit_id: int
    name: str
    kind: HabitKind
    period_scope: PeriodScope
    direction: Direction
    is_essential: bool
    total: Decimal
    target: Decimal
    met: bool


class DaySummary(BaseModel):
    date: date
    essentials_met: bool
    habits_met: int
    habits_total: int
    habits: list[HabitDayProgress]


class NeutralizedDayCreate(BaseModel):
    logical_date: date
    reason: str | None = None


class NeutralizedDayRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    logical_date: date
    reason: str | None
