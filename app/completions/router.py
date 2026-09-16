from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.completions import service
from app.completions.models import Completion
from app.completions.schemas import CompletionCreate, CompletionRead
from app.core.database import get_session
from app.habits import service as habits_service

router = APIRouter(prefix="/completions", tags=["completions"])


def get_completion_or_404(
    completion_id: int, session: Session = Depends(get_session)
) -> Completion:
    completion = service.get_completion(session, completion_id)
    if completion is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Completion not found")
    return completion


@router.post("", response_model=CompletionRead, status_code=status.HTTP_201_CREATED)
def create_completion(
    data: CompletionCreate, session: Session = Depends(get_session)
) -> Completion:
    habit = habits_service.get_habit(session, data.habit_id)
    if habit is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Habit not found")
    try:
        return service.create_completion(session, habit, data)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


@router.delete("/{completion_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_completion(
    completion: Completion = Depends(get_completion_or_404),
    session: Session = Depends(get_session),
) -> None:
    service.delete_completion(session, completion)
