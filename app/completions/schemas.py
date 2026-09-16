from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CompletionCreate(BaseModel):
    habit_id: int
    logical_date: date
    value: Decimal = Field(default=Decimal("1"), gt=0)


class CompletionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    habit_id: int
    logical_date: date
    value: Decimal
