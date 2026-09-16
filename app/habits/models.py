from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Enum, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.habits.enums import Direction, HabitKind, PeriodScope

class Habit(Base):
    __tablename__ = "habit"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)

    kind: Mapped[HabitKind] = mapped_column(Enum(HabitKind, name="habit_kind"))
    unit: Mapped[str | None] = mapped_column(String(20), default=None)

    period_scope: Mapped[PeriodScope] = mapped_column(Enum(PeriodScope, name="period_scope"))
    cadence: Mapped[int] = mapped_column(default=1)
    target: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    direction: Mapped[Direction] = mapped_column(
        Enum(Direction, name="direction"), default=Direction.AT_LEAST
    )

    is_essential: Mapped[bool] = mapped_column(default=False)

    active_from: Mapped[date]
    active_to: Mapped[date | None] = mapped_column(default=None)