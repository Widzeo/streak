from datetime import date
from decimal import Decimal

from app.habits.enums import Direction, PeriodScope
from app.stats.completeness import PeriodStatus
from app.stats.streaks import best_streak, compute_period_statuses, current_streak, streak

FAR_PAST = date(2020, 1, 1)


def test_compute_period_statuses_day_scope_returns_one_status_per_day():
    range_start = date(2026, 9, 14)
    range_end = date(2026, 9, 18)
    daily_totals = {
        date(2026, 9, 14): Decimal(1),
        date(2026, 9, 15): Decimal(0),
        date(2026, 9, 16): Decimal(1),
        date(2026, 9, 17): Decimal(1),
        date(2026, 9, 18): Decimal(0),
    }

    statuses = compute_period_statuses(
        PeriodScope.DAY,
        range_start,
        range_end,
        cadence=1,
        target=Decimal(1),
        direction=Direction.AT_LEAST,
        daily_totals=daily_totals,
        neutralized_dates=set(),
        active_from=FAR_PAST,
    )

    assert statuses == [
        PeriodStatus.COMPLETE,
        PeriodStatus.INCOMPLETE,
        PeriodStatus.COMPLETE,
        PeriodStatus.COMPLETE,
        PeriodStatus.INCOMPLETE,
    ]


def test_compute_period_statuses_week_scope_steps_one_period_at_a_time():
    # week 1: 2026-09-14..20 (3 hits -> complete)
    # week 2: 2026-09-21..27 (0 hits -> incomplete)
    # week 3: 2026-09-28..10-04 (0 hits -> incomplete)
    daily_totals = {
        date(2026, 9, 14): Decimal(1),
        date(2026, 9, 16): Decimal(1),
        date(2026, 9, 18): Decimal(1),
    }

    statuses = compute_period_statuses(
        PeriodScope.WEEK,
        range_start=date(2026, 9, 14),
        range_end=date(2026, 9, 28),
        cadence=3,
        target=Decimal(1),
        direction=Direction.AT_LEAST,
        daily_totals=daily_totals,
        neutralized_dates=set(),
        active_from=FAR_PAST,
    )

    assert statuses == [
        PeriodStatus.COMPLETE,
        PeriodStatus.INCOMPLETE,
        PeriodStatus.INCOMPLETE,
    ]


def test_current_streak_counts_a_trailing_run_of_complete_periods():
    statuses = [PeriodStatus.COMPLETE, PeriodStatus.COMPLETE, PeriodStatus.COMPLETE]
    assert current_streak(statuses) == 3


def test_current_streak_stops_at_the_most_recent_incomplete():
    statuses = [PeriodStatus.COMPLETE, PeriodStatus.COMPLETE, PeriodStatus.INCOMPLETE]
    assert current_streak(statuses) == 0


def test_current_streak_skips_neutralized_periods_without_breaking():
    statuses = [PeriodStatus.COMPLETE, PeriodStatus.NEUTRALIZED, PeriodStatus.COMPLETE]
    assert current_streak(statuses) == 2


def test_current_streak_neutralized_does_not_hide_an_older_incomplete():
    statuses = [PeriodStatus.INCOMPLETE, PeriodStatus.NEUTRALIZED, PeriodStatus.COMPLETE]
    assert current_streak(statuses) == 1


def test_current_streak_of_empty_history_is_zero():
    assert current_streak([]) == 0


def test_best_streak_finds_the_longest_run_not_just_the_trailing_one():
    statuses = [
        PeriodStatus.COMPLETE,
        PeriodStatus.COMPLETE,
        PeriodStatus.COMPLETE,
        PeriodStatus.INCOMPLETE,
        PeriodStatus.COMPLETE,
        PeriodStatus.COMPLETE,
    ]
    assert best_streak(statuses) == 3


def test_best_streak_neutralized_period_bridges_a_run_without_resetting_it():
    statuses = [
        PeriodStatus.COMPLETE,
        PeriodStatus.COMPLETE,
        PeriodStatus.NEUTRALIZED,
        PeriodStatus.COMPLETE,
    ]
    assert best_streak(statuses) == 3


def test_best_streak_neutralized_periods_alone_never_count():
    statuses = [PeriodStatus.NEUTRALIZED, PeriodStatus.NEUTRALIZED, PeriodStatus.NEUTRALIZED]
    assert best_streak(statuses) == 0


def test_best_streak_of_all_incomplete_is_zero():
    statuses = [PeriodStatus.INCOMPLETE, PeriodStatus.INCOMPLETE]
    assert best_streak(statuses) == 0


def test_streak_end_to_end_current_and_best_over_four_weeks():
    # week 1 (09-14..20): complete   \_ best run of 2
    # week 2 (09-21..27): complete   /
    # week 3 (09-28..10-04): incomplete (breaks the run)
    # week 4 (10-05..11): complete   -> current streak of 1
    daily_totals = {
        date(2026, 9, 14): Decimal(1),
        date(2026, 9, 16): Decimal(1),
        date(2026, 9, 18): Decimal(1),
        date(2026, 9, 21): Decimal(1),
        date(2026, 9, 23): Decimal(1),
        date(2026, 9, 25): Decimal(1),
        date(2026, 10, 5): Decimal(1),
        date(2026, 10, 7): Decimal(1),
        date(2026, 10, 9): Decimal(1),
    }

    result = streak(
        PeriodScope.WEEK,
        range_start=date(2026, 9, 14),
        range_end=date(2026, 10, 5),
        cadence=3,
        target=Decimal(1),
        direction=Direction.AT_LEAST,
        daily_totals=daily_totals,
        neutralized_dates=set(),
        active_from=FAR_PAST,
    )

    assert result.current == 1
    assert result.best == 2
