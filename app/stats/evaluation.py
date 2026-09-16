from decimal import Decimal

from app.habits.enums import Direction


def is_target_met(total: Decimal, target: Decimal, direction: Direction) -> bool:
    if direction == Direction.AT_LEAST:
        return total >= target
    return total <= target
