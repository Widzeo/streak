from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from app.habits.enums import Direction, PeriodScope
from app.stats.completeness import PeriodStatus, is_period_complete
from app.stats.periods import period_bounds


def compute_period_statuses(
    scope: PeriodScope,
    range_start: date,
    range_end: date,
    cadence: int,
    target: Decimal,
    direction: Direction,
    daily_totals: dict[date, Decimal],
    neutralized_dates: set[date],
) -> list[PeriodStatus]:
    """One status per period of `scope` overlapping [range_start, range_end], oldest first."""
    statuses = []
    current = range_start
    while current <= range_end:
        statuses.append(
            is_period_complete(
                scope, current, cadence, target, direction, daily_totals, neutralized_dates
            )
        )
        _, end = period_bounds(scope, current)
        current = end + timedelta(days=1)
    return statuses


def current_streak(statuses: list[PeriodStatus]) -> int:
    """Consecutive run ending at the last (most recent) status. NEUTRALIZED is skipped, not counted."""
    count = 0
    for status in reversed(statuses):
        if status == PeriodStatus.INCOMPLETE:
            break
        if status == PeriodStatus.COMPLETE:
            count += 1
    return count


def best_streak(statuses: list[PeriodStatus]) -> int:
    """Longest run anywhere in the sequence. NEUTRALIZED pauses a run without breaking or extending it."""
    best = 0
    running = 0
    for status in statuses:
        if status == PeriodStatus.INCOMPLETE:
            running = 0
        elif status == PeriodStatus.COMPLETE:
            running += 1
            best = max(best, running)
    return best


@dataclass
class Streak:
    current: int
    best: int


def streak(
    scope: PeriodScope,
    range_start: date,
    range_end: date,
    cadence: int,
    target: Decimal,
    direction: Direction,
    daily_totals: dict[date, Decimal],
    neutralized_dates: set[date],
) -> Streak:
    statuses = compute_period_statuses(
        scope, range_start, range_end, cadence, target, direction, daily_totals, neutralized_dates
    )
    return Streak(current=current_streak(statuses), best=best_streak(statuses))
