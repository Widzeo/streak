from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.habits.enums import Direction, HabitKind, PeriodScope


class HabitCreate(BaseModel):
    name: str
    kind: HabitKind
    unit: str | None = None
    period_scope: PeriodScope
    cadence: int = 1
    target: Decimal
    direction: Direction = Direction.AT_LEAST
    is_essential: bool = False
    active_from: date


class HabitUpdate(BaseModel):
    name: str | None = None
    kind: HabitKind | None = None
    unit: str | None = None
    period_scope: PeriodScope | None = None
    cadence: int | None = None
    target: Decimal | None = None
    direction: Direction | None = None
    is_essential: bool | None = None
    active_from: date | None = None


class HabitRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    kind: HabitKind
    unit: str | None
    period_scope: PeriodScope
    cadence: int
    target: Decimal
    direction: Direction
    is_essential: bool
    active_from: date
    active_to: date | None
