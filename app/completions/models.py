from datetime import date
from decimal import Decimal

from sqlalchemy import ForeignKey, Index, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Completion(Base):
    __tablename__ = "completion"
    __table_args__ = (Index("ix_completion_habit_id_logical_date", "habit_id", "logical_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    habit_id: Mapped[int] = mapped_column(ForeignKey("habit.id"))
    logical_date: Mapped[date]
    value: Mapped[Decimal] = mapped_column(Numeric(12, 2))
