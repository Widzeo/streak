from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.habits import service
from app.habits.models import Category, Habit
from app.habits.schemas import (
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
    HabitCreate,
    HabitRead,
    HabitUpdate,
)

router = APIRouter(prefix="/habits", tags=["habits"])
categories_router = APIRouter(prefix="/categories", tags=["categories"])


def get_habit_or_404(habit_id: int, session: Session = Depends(get_session)) -> Habit:
    habit = service.get_habit(session, habit_id)
    if habit is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Habit not found")
    return habit


def get_category_or_404(category_id: int, session: Session = Depends(get_session)) -> Category:
    category = service.get_category(session, category_id)
    if category is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Category not found")
    return category


@router.post("", response_model=HabitRead, status_code=status.HTTP_201_CREATED)
def create_habit(data: HabitCreate, session: Session = Depends(get_session)) -> Habit:
    try:
        return service.create_habit(session, data)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


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


@categories_router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(data: CategoryCreate, session: Session = Depends(get_session)) -> Category:
    return service.create_category(session, data)


@categories_router.get("", response_model=list[CategoryRead])
def list_categories(session: Session = Depends(get_session)) -> list[Category]:
    return service.list_categories(session)


@categories_router.patch("/{category_id}", response_model=CategoryRead)
def update_category(
    data: CategoryUpdate,
    category: Category = Depends(get_category_or_404),
    session: Session = Depends(get_session),
) -> Category:
    return service.update_category(session, category, data)


@categories_router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category: Category = Depends(get_category_or_404),
    session: Session = Depends(get_session),
) -> None:
    service.delete_category(session, category)
