from datetime import date

from app.core.dates import month_bounds, week_bounds, year_bounds
from app.habits.enums import PeriodScope


def period_bounds(scope: PeriodScope, on_date: date) -> tuple[date, date]:
    if scope == PeriodScope.DAY:
        return on_date, on_date
    if scope == PeriodScope.WEEK:
        return week_bounds(on_date)
    if scope == PeriodScope.MONTH:
        return month_bounds(on_date)
    return year_bounds(on_date)
