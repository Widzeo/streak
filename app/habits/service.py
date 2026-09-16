from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.habits.models import Category, Habit
from app.habits.schemas import CategoryCreate, CategoryUpdate, HabitCreate, HabitUpdate
from app.habits.validation import check_habit_invariants


def create_habit(session: Session, data: HabitCreate) -> Habit:
    if data.category_id is not None and get_category(session, data.category_id) is None:
        raise ValueError("category not found")

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

    if "category_id" in updates and updates["category_id"] is not None:
        if get_category(session, updates["category_id"]) is None:
            raise ValueError("category not found")

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


def create_category(session: Session, data: CategoryCreate) -> Category:
    category = Category(name=data.name)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


def list_categories(session: Session) -> list[Category]:
    return list(session.scalars(select(Category).order_by(Category.id)))


def get_category(session: Session, category_id: int) -> Category | None:
    return session.get(Category, category_id)


def update_category(session: Session, category: Category, data: CategoryUpdate) -> Category:
    category.name = data.name
    session.commit()
    session.refresh(category)
    return category


def delete_category(session: Session, category: Category) -> None:
    session.delete(category)
    session.commit()
