from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.completions.models import Completion
from app.completions.schemas import CompletionCreate, CompletionHistoryEntry, CompletionHistoryPage
from app.habits.models import Habit


def create_completion(session: Session, habit: Habit, data: CompletionCreate) -> Completion:
    if data.logical_date < habit.active_from or (
        habit.active_to is not None and data.logical_date > habit.active_to
    ):
        raise ValueError("logical_date is outside the habit's active period")

    completion = Completion(
        habit_id=habit.id, logical_date=data.logical_date, value=data.value
    )
    session.add(completion)
    session.commit()
    session.refresh(completion)
    return completion


def get_completion(session: Session, completion_id: int) -> Completion | None:
    return session.get(Completion, completion_id)


def delete_completion(session: Session, completion: Completion) -> None:
    session.delete(completion)
    session.commit()


def list_history(
    session: Session, habit_id: int | None, limit: int, offset: int
) -> CompletionHistoryPage:
    filters = []
    if habit_id is not None:
        filters.append(Completion.habit_id == habit_id)

    total = session.scalar(select(func.count()).select_from(Completion).where(*filters)) or 0

    rows = session.execute(
        select(
            Completion.id,
            Completion.habit_id,
            Habit.name,
            Completion.logical_date,
            Completion.value,
        )
        .join(Habit, Habit.id == Completion.habit_id)
        .where(*filters)
        .order_by(Completion.logical_date.desc(), Completion.id.desc())
        .limit(limit)
        .offset(offset)
    )

    items = [
        CompletionHistoryEntry(
            id=row.id,
            habit_id=row.habit_id,
            habit_name=row.name,
            logical_date=row.logical_date,
            value=row.value,
        )
        for row in rows
    ]

    return CompletionHistoryPage(items=items, total=total, limit=limit, offset=offset)
