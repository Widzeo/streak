from datetime import date
from decimal import Decimal

from app.habits.enums import HabitKind, PeriodScope


def check_habit_invariants(
    kind: HabitKind,
    target: Decimal,
    period_scope: PeriodScope,
    cadence: int,
    active_from: date,
    active_to: date | None,
) -> None:
    if kind == HabitKind.BINARY and target != 1:
        raise ValueError("a binary habit must have a target of 1")

    if cadence < 1:
        raise ValueError("cadence must be at least 1")

    if period_scope == PeriodScope.DAY and cadence != 1:
        raise ValueError(
            "cadence must be 1 when period_scope is day: a day has no distinct "
            "sub-occurrences to count"
        )

    if active_to is not None and active_to < active_from:
        raise ValueError("active_to must be on or after active_from")
