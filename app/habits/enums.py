from enum import StrEnum

class HabitKind(StrEnum):
    BINARY = "binary"
    QUANTIFIED = "quantified"

class PeriodScope(StrEnum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"

class Direction(StrEnum):
    AT_LEAST = "at_least"
    AT_MOST = "at_most"