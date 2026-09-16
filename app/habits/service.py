from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.habits.models import Habit
from app.habits.schemas import HabitCreate, HabitUpdate
from app.habits.validation import check_habit_invariants


def create_habit(session: Session, data: HabitCreate) -> Habit:
    habit = Habit(**data.model_dump())
    session.add(habit)
    session.commit()
    session.refresh(habit)
    return habit


def list_habits(session: Session) -> list[Habit]:
    return list(session.scalars(select(Habit).order_by(Habit.id)))


def get_habit(session: Session, habit_id: int) -> Habit | None:
    return session.get(Habit, habit_id)


def update_habit(session: Session, habit: Habit, data: HabitUpdate) -> Habit:
    updates = data.model_dump(exclude_unset=True)
    check_habit_invariants(
        kind=updates.get("kind", habit.kind),
        target=updates.get("target", habit.target),
        period_scope=updates.get("period_scope", habit.period_scope),
        cadence=updates.get("cadence", habit.cadence),
        active_from=updates.get("active_from", habit.active_from),
        active_to=updates.get("active_to", habit.active_to),
    )
    for field, value in updates.items():
        setattr(habit, field, value)
    session.commit()
    session.refresh(habit)
    return habit


def deactivate_habit(session: Session, habit: Habit) -> Habit:
    habit.active_to = date.today()
    session.commit()
    session.refresh(habit)
    return habit
