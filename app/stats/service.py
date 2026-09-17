from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.completions.models import Completion
from app.habits.models import Habit
from app.stats.completeness import PeriodStatus, count_days_met, is_period_complete
from app.stats.models import NeutralizedDay
from app.stats.periods import period_bounds
from app.stats.schemas import (
    DayHeatmapEntry,
    DaySummary,
    HabitDayProgress,
    HabitStats,
    NeutralizedDayCreate,
    StreakSummary,
    StreaksOverview,
    YearHeatmap,
)
from app.stats.streaks import Streak, streak


def get_active_habits(session: Session, on_date: date) -> list[Habit]:
    return list(
        session.scalars(
            select(Habit).where(
                Habit.active_from <= on_date,
                (Habit.active_to.is_(None)) | (Habit.active_to >= on_date),
            )
        )
    )


def get_daily_totals(
    session: Session, habit_id: int, start: date, end: date
) -> dict[date, Decimal]:
    rows = session.execute(
        select(Completion.logical_date, func.sum(Completion.value))
        .where(
            Completion.habit_id == habit_id,
            Completion.logical_date >= start,
            Completion.logical_date <= end,
        )
        .group_by(Completion.logical_date)
    )
    return dict(rows.all())


def get_neutralized_dates(session: Session, start: date, end: date) -> set[date]:
    return set(
        session.scalars(
            select(NeutralizedDay.logical_date).where(
                NeutralizedDay.logical_date >= start,
                NeutralizedDay.logical_date <= end,
            )
        )
    )


def get_habit_day_progress(session: Session, habit: Habit, on_date: date) -> HabitDayProgress:
    start, end = period_bounds(habit.period_scope, on_date)
    daily_totals = get_daily_totals(session, habit.id, start, end)
    neutralized_dates = get_neutralized_dates(session, start, end)

    status = is_period_complete(
        habit.period_scope,
        on_date,
        habit.cadence,
        habit.target,
        habit.direction,
        daily_totals,
        neutralized_dates,
        habit.active_from,
        habit.active_to,
    )
    days_met = count_days_met(
        habit.period_scope,
        on_date,
        habit.target,
        habit.direction,
        daily_totals,
        neutralized_dates,
        habit.active_from,
        habit.active_to,
    )

    return HabitDayProgress(
        habit_id=habit.id,
        name=habit.name,
        kind=habit.kind,
        period_scope=habit.period_scope,
        direction=habit.direction,
        is_essential=habit.is_essential,
        today_total=daily_totals.get(on_date, Decimal(0)),
        target=habit.target,
        cadence=habit.cadence,
        days_met=days_met,
        status=status,
    )


def get_day_summary(session: Session, on_date: date) -> DaySummary:
    habits = get_active_habits(session, on_date)
    progress = [get_habit_day_progress(session, habit, on_date) for habit in habits]

    # a neutralized habit is neither a success nor a failure: it is left out
    # of the ratio entirely, same as it would be out of a streak.
    evaluable = [p for p in progress if p.status != PeriodStatus.NEUTRALIZED]
    essentials = [p for p in evaluable if p.is_essential]
    essentials_met = all(p.status == PeriodStatus.COMPLETE for p in essentials)

    return DaySummary(
        date=on_date,
        essentials_met=essentials_met,
        habits_met=sum(1 for p in evaluable if p.status == PeriodStatus.COMPLETE),
        habits_total=len(evaluable),
        habits=progress,
    )


def get_habit_streak(session: Session, habit: Habit, today: date) -> Streak:
    # today never counts towards the streak - it stops at yesterday
    range_end = today - timedelta(days=1)
    if habit.active_to is not None:
        range_end = min(range_end, habit.active_to)
    range_start = habit.active_from

    if range_start > range_end:
        return Streak(current=0, best=0)

    daily_totals = get_daily_totals(session, habit.id, range_start, range_end)
    neutralized_dates = get_neutralized_dates(session, range_start, range_end)

    return streak(
        habit.period_scope,
        range_start,
        range_end,
        habit.cadence,
        habit.target,
        habit.direction,
        daily_totals,
        neutralized_dates,
        habit.active_from,
        habit.active_to,
    )


def get_habit_stats(session: Session, habit: Habit, today: date) -> HabitStats:
    result = get_habit_streak(session, habit, today)
    today_progress = get_habit_day_progress(session, habit, today)

    return HabitStats(
        habit_id=habit.id,
        name=habit.name,
        current_streak=result.current,
        best_streak=result.best,
        today=today_progress,
    )


def get_streaks_overview(session: Session, today: date) -> StreaksOverview:
    habits = get_active_habits(session, today)
    summaries = []
    for habit in habits:
        result = get_habit_streak(session, habit, today)
        summaries.append(
            StreakSummary(
                habit_id=habit.id,
                name=habit.name,
                current_streak=result.current,
                best_streak=result.best,
            )
        )
    return StreaksOverview(date=today, streaks=summaries)


def get_year_heatmap(session: Session, year: int) -> YearHeatmap:
    year_start = date(year, 1, 1)
    year_end = date(year, 12, 31)
    # a week-scope period can straddle the year boundary (e.g. the week of
    # Dec 29 - Jan 4): pad the fetch range by a week on each side so those
    # periods are evaluated with complete data, not a truncated view.
    buffer = timedelta(days=6)
    fetch_start = year_start - buffer
    fetch_end = year_end + buffer

    habits = list(
        session.scalars(
            select(Habit).where(
                Habit.active_from <= year_end,
                (Habit.active_to.is_(None)) | (Habit.active_to >= year_start),
            )
        )
    )

    neutralized_dates = get_neutralized_dates(session, fetch_start, fetch_end)

    totals_by_habit: dict[int, dict[date, Decimal]] = {}
    if habits:
        rows = session.execute(
            select(Completion.habit_id, Completion.logical_date, func.sum(Completion.value))
            .where(
                Completion.habit_id.in_([h.id for h in habits]),
                Completion.logical_date >= fetch_start,
                Completion.logical_date <= fetch_end,
            )
            .group_by(Completion.habit_id, Completion.logical_date)
        )
        for habit_id, logical_date, total in rows:
            totals_by_habit.setdefault(habit_id, {})[logical_date] = total

    today = date.today()

    days = []
    current = year_start
    while current <= year_end:
        # a day that hasn't happened yet can't be evaluated - showing it as
        # "no data" avoids habits with a lenient at_most/cadence=1 target
        # trivially reading as complete on days nothing could have occurred.
        if current > today:
            days.append(
                DayHeatmapEntry(date=current, habits_met=0, habits_total=0, complete=False)
            )
            current += timedelta(days=1)
            continue

        active_habits = [
            h
            for h in habits
            if h.active_from <= current and (h.active_to is None or h.active_to >= current)
        ]

        met = 0
        total_count = 0
        for habit in active_habits:
            status = is_period_complete(
                habit.period_scope,
                current,
                habit.cadence,
                habit.target,
                habit.direction,
                totals_by_habit.get(habit.id, {}),
                neutralized_dates,
                habit.active_from,
                habit.active_to,
            )
            if status == PeriodStatus.NEUTRALIZED:
                continue
            total_count += 1
            if status == PeriodStatus.COMPLETE:
                met += 1

        days.append(
            DayHeatmapEntry(
                date=current,
                habits_met=met,
                habits_total=total_count,
                complete=total_count > 0 and met == total_count,
            )
        )
        current += timedelta(days=1)

    return YearHeatmap(year=year, days=days)


def get_neutralized_day(session: Session, on_date: date) -> NeutralizedDay | None:
    return session.get(NeutralizedDay, on_date)


def is_neutralized(session: Session, on_date: date) -> bool:
    return get_neutralized_day(session, on_date) is not None


def create_neutralized_day(session: Session, data: NeutralizedDayCreate) -> NeutralizedDay:
    if get_neutralized_day(session, data.logical_date) is not None:
        raise ValueError("this date is already neutralized")

    neutralized = NeutralizedDay(logical_date=data.logical_date, reason=data.reason)
    session.add(neutralized)
    session.commit()
    session.refresh(neutralized)
    return neutralized


def delete_neutralized_day(session: Session, neutralized: NeutralizedDay) -> None:
    session.delete(neutralized)
    session.commit()
