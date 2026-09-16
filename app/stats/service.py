from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.completions.models import Completion
from app.habits.models import Habit
from app.stats.evaluation import is_target_met
from app.stats.periods import period_bounds
from app.stats.schemas import DaySummary, HabitDayProgress


def get_active_habits(session: Session, on_date: date) -> list[Habit]:
    return list(
        session.scalars(
            select(Habit).where(
                Habit.active_from <= on_date,
                (Habit.active_to.is_(None)) | (Habit.active_to >= on_date),
            )
        )
    )


def get_day_summary(session: Session, on_date: date) -> DaySummary:
    habits = get_active_habits(session, on_date)

    progress = []
    for habit in habits:
        start, end = period_bounds(habit.period_scope, on_date)
        total = session.scalar(
            select(func.coalesce(func.sum(Completion.value), 0)).where(
                Completion.habit_id == habit.id,
                Completion.logical_date >= start,
                Completion.logical_date <= end,
            )
        )
        met = is_target_met(total, habit.target, habit.direction)
        progress.append(
            HabitDayProgress(
                habit_id=habit.id,
                name=habit.name,
                kind=habit.kind,
                period_scope=habit.period_scope,
                direction=habit.direction,
                is_essential=habit.is_essential,
                total=total,
                target=habit.target,
                met=met,
            )
        )

    essentials = [p for p in progress if p.is_essential]
    essentials_met = all(p.met for p in essentials)

    return DaySummary(
        date=on_date,
        essentials_met=essentials_met,
        habits_met=sum(1 for p in progress if p.met),
        habits_total=len(progress),
        habits=progress,
    )
