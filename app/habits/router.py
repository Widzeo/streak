from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.habits import service
from app.habits.models import Habit
from app.habits.schemas import HabitCreate, HabitRead, HabitUpdate

router = APIRouter(prefix="/habits", tags=["habits"])


def get_habit_or_404(habit_id: int, session: Session = Depends(get_session)) -> Habit:
    habit = service.get_habit(session, habit_id)
    if habit is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Habit not found")
    return habit


@router.post("", response_model=HabitRead, status_code=status.HTTP_201_CREATED)
def create_habit(data: HabitCreate, session: Session = Depends(get_session)) -> Habit:
    return service.create_habit(session, data)


@router.get("", response_model=list[HabitRead])
def list_habits(session: Session = Depends(get_session)) -> list[Habit]:
    return service.list_habits(session)


@router.get("/{habit_id}", response_model=HabitRead)
def get_habit(habit: Habit = Depends(get_habit_or_404)) -> Habit:
    return habit


@router.patch("/{habit_id}", response_model=HabitRead)
def update_habit(
    data: HabitUpdate,
    habit: Habit = Depends(get_habit_or_404),
    session: Session = Depends(get_session),
) -> Habit:
    try:
        return service.update_habit(session, habit, data)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


@router.delete("/{habit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_habit(
    habit: Habit = Depends(get_habit_or_404),
    session: Session = Depends(get_session),
) -> None:
    service.deactivate_habit(session, habit)
