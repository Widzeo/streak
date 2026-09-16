import calendar
from datetime import date, timedelta


def week_bounds(on_date: date) -> tuple[date, date]:
    start = on_date - timedelta(days=on_date.weekday())
    end = start + timedelta(days=6)
    return start, end


def month_bounds(on_date: date) -> tuple[date, date]:
    start = on_date.replace(day=1)
    last_day = calendar.monthrange(on_date.year, on_date.month)[1]
    end = on_date.replace(day=last_day)
    return start, end


def year_bounds(on_date: date) -> tuple[date, date]:
    return date(on_date.year, 1, 1), date(on_date.year, 12, 31)
