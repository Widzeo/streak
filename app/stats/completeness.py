from datetime import date, timedelta
from decimal import Decimal
from enum import StrEnum

from app.habits.enums import Direction, PeriodScope
from app.stats.evaluation import is_target_met
from app.stats.periods import period_bounds


class PeriodStatus(StrEnum):
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"
    NEUTRALIZED = "neutralized"


def eligible_days(
    scope: PeriodScope,
    on_date: date,
    neutralized_dates: set[date],
    active_from: date,
    active_to: date | None = None,
) -> list[date]:
    """Days of the period containing `on_date` that count towards cadence:
    within the habit's active window and not neutralized."""
    start, end = period_bounds(scope, on_date)
    start = max(start, active_from)
    if active_to is not None:
        end = min(end, active_to)

    if start > end:
        # the habit was not active during any part of this period
        return []

    days = [start + timedelta(days=n) for n in range((end - start).days + 1)]
    return [d for d in days if d not in neutralized_dates]


def count_days_met(
    scope: PeriodScope,
    on_date: date,
    target: Decimal,
    direction: Direction,
    daily_totals: dict[date, Decimal],
    neutralized_dates: set[date],
    active_from: date,
    active_to: date | None = None,
) -> int:
    days = eligible_days(scope, on_date, neutralized_dates, active_from, active_to)
    return sum(
        1 for d in days if is_target_met(daily_totals.get(d, Decimal(0)), target, direction)
    )


def is_period_complete(
    scope: PeriodScope,
    on_date: date,
    cadence: int,
    target: Decimal,
    direction: Direction,
    daily_totals: dict[date, Decimal],
    neutralized_dates: set[date],
    active_from: date,
    active_to: date | None = None,
) -> PeriodStatus:
    days = eligible_days(scope, on_date, neutralized_dates, active_from, active_to)
    if not days:
        return PeriodStatus.NEUTRALIZED

    days_met = count_days_met(
        scope, on_date, target, direction, daily_totals, neutralized_dates, active_from, active_to
    )
    return PeriodStatus.COMPLETE if days_met >= cadence else PeriodStatus.INCOMPLETE
