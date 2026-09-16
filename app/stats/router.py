from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.stats import service
from app.stats.models import NeutralizedDay
from app.stats.schemas import DaySummary, NeutralizedDayCreate, NeutralizedDayRead

router = APIRouter(tags=["stats"])


@router.get("/days/{on_date}", response_model=DaySummary)
def get_day(on_date: date, session: Session = Depends(get_session)) -> DaySummary:
    return service.get_day_summary(session, on_date)


def get_neutralized_day_or_404(
    on_date: date, session: Session = Depends(get_session)
) -> NeutralizedDay:
    neutralized = service.get_neutralized_day(session, on_date)
    if neutralized is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Neutralized day not found")
    return neutralized


@router.post(
    "/neutralized-days",
    response_model=NeutralizedDayRead,
    status_code=status.HTTP_201_CREATED,
)
def create_neutralized_day(
    data: NeutralizedDayCreate, session: Session = Depends(get_session)
) -> NeutralizedDay:
    try:
        return service.create_neutralized_day(session, data)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


@router.delete("/neutralized-days/{on_date}", status_code=status.HTTP_204_NO_CONTENT)
def delete_neutralized_day(
    neutralized: NeutralizedDay = Depends(get_neutralized_day_or_404),
    session: Session = Depends(get_session),
) -> None:
    service.delete_neutralized_day(session, neutralized)
