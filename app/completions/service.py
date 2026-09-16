from sqlalchemy.orm import Session

from app.completions.models import Completion
from app.completions.schemas import CompletionCreate
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
    