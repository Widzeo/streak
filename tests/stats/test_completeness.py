from datetime import date
from decimal import Decimal

from app.habits.enums import Direction, PeriodScope
from app.stats.completeness import PeriodStatus, is_period_complete

FAR_PAST = date(2020, 1, 1)  # a habit "always active" for tests not about active_from/active_to

# the ISO week of 2026-09-14 (Mon) .. 2026-09-20 (Sun)
MON, TUE, WED, THU, FRI, SAT, SUN = (
    date(2026, 9, 14),
    date(2026, 9, 15),
    date(2026, 9, 16),
    date(2026, 9, 17),
    date(2026, 9, 18),
    date(2026, 9, 19),
    date(2026, 9, 20),
)


def test_day_scope_target_met_is_complete():
    status = is_period_complete(
        PeriodScope.DAY,
        WED,
        cadence=1,
        target=Decimal(1),
        direction=Direction.AT_LEAST,
        daily_totals={WED: Decimal(1)},
        neutralized_dates=set(),
        active_from=FAR_PAST,
    )
    assert status == PeriodStatus.COMPLETE


def test_day_scope_target_not_met_is_incomplete():
    status = is_period_complete(
        PeriodScope.DAY,
        WED,
        cadence=1,
        target=Decimal(1),
        direction=Direction.AT_LEAST,
        daily_totals={WED: Decimal(0)},
        neutralized_dates=set(),
        active_from=FAR_PAST,
    )
    assert status == PeriodStatus.INCOMPLETE


def test_day_scope_neutralized_day_is_neutralized():
    status = is_period_complete(
        PeriodScope.DAY,
        WED,
        cadence=1,
        target=Decimal(1),
        direction=Direction.AT_LEAST,
        daily_totals={WED: Decimal(0)},
        neutralized_dates={WED},
        active_from=FAR_PAST,
    )
    assert status == PeriodStatus.NEUTRALIZED


def test_week_scope_exact_cadence_met_is_complete():
    status = is_period_complete(
        PeriodScope.WEEK,
        WED,
        cadence=3,
        target=Decimal(1),
        direction=Direction.AT_LEAST,
        daily_totals={MON: Decimal(1), WED: Decimal(1), FRI: Decimal(1)},
        neutralized_dates=set(),
        active_from=FAR_PAST,
    )
    assert status == PeriodStatus.COMPLETE


def test_week_scope_below_cadence_is_incomplete():
    status = is_period_complete(
        PeriodScope.WEEK,
        WED,
        cadence=3,
        target=Decimal(1),
        direction=Direction.AT_LEAST,
        daily_totals={MON: Decimal(1), WED: Decimal(1)},
        neutralized_dates=set(),
        active_from=FAR_PAST,
    )
    assert status == PeriodStatus.INCOMPLETE


def test_week_scope_above_cadence_is_still_complete():
    status = is_period_complete(
        PeriodScope.WEEK,
        WED,
        cadence=3,
        target=Decimal(1),
        direction=Direction.AT_LEAST,
        daily_totals={
            MON: Decimal(1),
            TUE: Decimal(1),
            WED: Decimal(1),
            THU: Decimal(1),
            FRI: Decimal(1),
        },
        neutralized_dates=set(),
        active_from=FAR_PAST,
    )
    assert status == PeriodStatus.COMPLETE


def test_week_scope_neutralizing_unmet_day_does_not_reduce_cadence_requirement():
    # Sunday is neutralized, but cadence stays 3 - it is not lowered to account
    # for having one less eligible day in the week.
    status = is_period_complete(
        PeriodScope.WEEK,
        WED,
        cadence=3,
        target=Decimal(1),
        direction=Direction.AT_LEAST,
        daily_totals={MON: Decimal(1), WED: Decimal(1), FRI: Decimal(1)},
        neutralized_dates={SUN},
        active_from=FAR_PAST,
    )
    assert status == PeriodStatus.COMPLETE


def test_week_scope_fully_neutralized_week_is_neutralized():
    status = is_period_complete(
        PeriodScope.WEEK,
        WED,
        cadence=3,
        target=Decimal(1),
        direction=Direction.AT_LEAST,
        daily_totals={},
        neutralized_dates={MON, TUE, WED, THU, FRI, SAT, SUN},
        active_from=FAR_PAST,
    )
    assert status == PeriodStatus.NEUTRALIZED


def test_week_scope_missing_daily_totals_default_to_zero():
    # no entries at all for the week: every day defaults to 0, not a crash
    status = is_period_complete(
        PeriodScope.WEEK,
        WED,
        cadence=3,
        target=Decimal(1),
        direction=Direction.AT_LEAST,
        daily_totals={},
        neutralized_dates=set(),
        active_from=FAR_PAST,
    )
    assert status == PeriodStatus.INCOMPLETE


def test_missing_day_leaves_period_incomplete():
    status = is_period_complete(
        PeriodScope.WEEK,
        WED,
        cadence=3,
        target=Decimal(1),
        direction=Direction.AT_LEAST,
        daily_totals={MON: Decimal(1), WED: Decimal(1)},
        neutralized_dates=set(),
        active_from=FAR_PAST,
    )
    assert status == PeriodStatus.INCOMPLETE


def test_retroactively_filled_day_completes_period():
    # same week as above, but the Friday entry has since been logged retroactively
    status = is_period_complete(
        PeriodScope.WEEK,
        WED,
        cadence=3,
        target=Decimal(1),
        direction=Direction.AT_LEAST,
        daily_totals={MON: Decimal(1), WED: Decimal(1), FRI: Decimal(1)},
        neutralized_dates=set(),
        active_from=FAR_PAST,
    )
    assert status == PeriodStatus.COMPLETE


def test_habit_added_mid_week_excludes_pre_active_days():
    # active_from is Wednesday: Monday and Tuesday must not count as missed days
    status = is_period_complete(
        PeriodScope.WEEK,
        WED,
        cadence=3,
        target=Decimal(1),
        direction=Direction.AT_LEAST,
        daily_totals={WED: Decimal(1), THU: Decimal(1), FRI: Decimal(1)},
        neutralized_dates=set(),
        active_from=WED,
    )
    assert status == PeriodStatus.COMPLETE


def test_habit_added_mid_week_still_requires_real_cadence():
    # only 2 of the 5 eligible days (Wed..Sun) meet the target: still incomplete
    status = is_period_complete(
        PeriodScope.WEEK,
        WED,
        cadence=3,
        target=Decimal(1),
        direction=Direction.AT_LEAST,
        daily_totals={WED: Decimal(1), THU: Decimal(1)},
        neutralized_dates=set(),
        active_from=WED,
    )
    assert status == PeriodStatus.INCOMPLETE


def test_habit_deactivated_mid_week_excludes_post_deactivation_days():
    # active_to is Thursday: Friday..Sunday must not be required
    status = is_period_complete(
        PeriodScope.WEEK,
        WED,
        cadence=3,
        target=Decimal(1),
        direction=Direction.AT_LEAST,
        daily_totals={MON: Decimal(1), TUE: Decimal(1), WED: Decimal(1)},
        neutralized_dates=set(),
        active_from=FAR_PAST,
        active_to=THU,
    )
    assert status == PeriodStatus.COMPLETE


def test_period_entirely_before_active_from_is_neutralized():
    on_date = date(2026, 8, 10)  # a week entirely in August
    status = is_period_complete(
        PeriodScope.WEEK,
        on_date,
        cadence=1,
        target=Decimal(1),
        direction=Direction.AT_LEAST,
        daily_totals={},
        neutralized_dates=set(),
        active_from=date(2026, 9, 1),
    )
    assert status == PeriodStatus.NEUTRALIZED


def test_at_most_direction_with_cadence_counts_days_under_budget():
    # "spend at most 50/day, at least 5 days a week"
    status = is_period_complete(
        PeriodScope.WEEK,
        WED,
        cadence=5,
        target=Decimal(50),
        direction=Direction.AT_MOST,
        daily_totals={
            MON: Decimal(30),
            TUE: Decimal(60),
            WED: Decimal(40),
            THU: Decimal(20),
            FRI: Decimal(45),
            SAT: Decimal(70),
            SUN: Decimal(10),
        },
        neutralized_dates=set(),
        active_from=FAR_PAST,
    )
    assert status == PeriodStatus.COMPLETE
