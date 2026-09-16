from datetime import date
from decimal import Decimal

from pydantic import BaseModel

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
