from datetime import date
from decimal import Decimal
from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator

from app.habits.enums import Direction, HabitKind, PeriodScope
from app.habits.validation import check_habit_invariants


class HabitCreate(BaseModel):
    name: str
    kind: HabitKind
    unit: str | None = None
    period_scope: PeriodScope
    cadence: int = 1
    target: Decimal
    direction: Direction = Direction.AT_LEAST
    is_essential: bool = False
    category_id: int | None = None
    active_from: date

    @model_validator(mode="after")
    def check_invariants(self) -> Self:
        check_habit_invariants(
            kind=self.kind,
            target=self.target,
            period_scope=self.period_scope,
            cadence=self.cadence,
            active_from=self.active_from,
            active_to=None,
        )
        return self


class HabitUpdate(BaseModel):
    name: str | None = None
    kind: HabitKind | None = None
    unit: str | None = None
    period_scope: PeriodScope | None = None
    cadence: int | None = None
    target: Decimal | None = None
    direction: Direction | None = None
    is_essential: bool | None = None
    category_id: int | None = None
    active_from: date | None = None
    active_to: date | None = None

    @model_validator(mode="after")
    def check_active_range(self) -> Self:
        if (
            self.active_from is not None
            and self.active_to is not None
            and self.active_to < self.active_from
        ):
            raise ValueError("active_to must be on or after active_from")
        return self


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
    category_id: int | None
    active_from: date
    active_to: date | None


class CategoryCreate(BaseModel):
    name: str


class CategoryUpdate(BaseModel):
    name: str


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
