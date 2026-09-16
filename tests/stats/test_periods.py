from datetime import date

from app.habits.enums import PeriodScope
from app.stats.periods import period_bounds


def test_day_scope_bounds_are_the_date_itself():
    on_date = date(2026, 9, 16)
    assert period_bounds(PeriodScope.DAY, on_date) == (on_date, on_date)


def test_week_scope_bounds_start_on_monday():
    # 2026-09-16 is a Wednesday
    on_date = date(2026, 9, 16)
    assert period_bounds(PeriodScope.WEEK, on_date) == (date(2026, 9, 14), date(2026, 9, 20))


def test_week_scope_on_a_monday_is_its_own_start():
    on_date = date(2026, 9, 14)
    assert period_bounds(PeriodScope.WEEK, on_date) == (date(2026, 9, 14), date(2026, 9, 20))


def test_week_scope_on_a_sunday_is_its_own_end():
    on_date = date(2026, 9, 20)
    assert period_bounds(PeriodScope.WEEK, on_date) == (date(2026, 9, 14), date(2026, 9, 20))


def test_week_scope_straddling_two_months():
    # 2026-02-28 is a Saturday: its week starts in February and ends in March
    on_date = date(2026, 2, 28)
    assert period_bounds(PeriodScope.WEEK, on_date) == (date(2026, 2, 23), date(2026, 3, 1))


def test_month_scope_bounds_for_a_31_day_month():
    on_date = date(2026, 1, 15)
    assert period_bounds(PeriodScope.MONTH, on_date) == (date(2026, 1, 1), date(2026, 1, 31))


def test_month_scope_bounds_for_february_non_leap_year():
    on_date = date(2026, 2, 10)
    assert period_bounds(PeriodScope.MONTH, on_date) == (date(2026, 2, 1), date(2026, 2, 28))


def test_month_scope_bounds_for_february_leap_year():
    on_date = date(2028, 2, 10)
    assert period_bounds(PeriodScope.MONTH, on_date) == (date(2028, 2, 1), date(2028, 2, 29))


def test_year_scope_bounds():
    on_date = date(2026, 7, 4)
    assert period_bounds(PeriodScope.YEAR, on_date) == (date(2026, 1, 1), date(2026, 12, 31))
