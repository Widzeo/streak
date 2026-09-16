from datetime import date

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class NeutralizedDay(Base):
    __tablename__ = "neutralized_day"

    logical_date: Mapped[date] = mapped_column(primary_key=True)
    reason: Mapped[str | None] = mapped_column(String(200), default=None)
