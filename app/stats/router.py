from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.stats import service
from app.stats.schemas import DaySummary

router = APIRouter(tags=["stats"])


@router.get("/days/{on_date}", response_model=DaySummary)
def get_day(on_date: date, session: Session = Depends(get_session)) -> DaySummary:
    return service.get_day_summary(session, on_date)
