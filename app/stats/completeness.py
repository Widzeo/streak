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


def is_period_complete(
    scope: PeriodScope,
    on_date: date,
    cadence: int,
    target: Decimal,
    direction: Direction,
    daily_totals: dict[date, Decimal],
    neutralized_dates: set[date],
) -> PeriodStatus:
    start, end = period_bounds(scope, on_date)
    days = [start + timedelta(days=n) for n in range((end - start).days + 1)]
    eligible_days = [d for d in days if d not in neutralized_dates]

    if not eligible_days:
        return PeriodStatus.NEUTRALIZED

    days_met = sum(
        1
        for d in eligible_days
        if is_target_met(daily_totals.get(d, Decimal(0)), target, direction)
    )
    return PeriodStatus.COMPLETE if days_met >= cadence else PeriodStatus.INCOMPLETE
