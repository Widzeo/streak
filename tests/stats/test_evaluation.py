from decimal import Decimal

import pytest

from app.habits.enums import Direction
from app.stats.evaluation import is_target_met


@pytest.mark.parametrize(
    "total,target,direction,expected",
    [
        # at_least: met once the total reaches the target, boundary included
        (Decimal("3"), Decimal("2.7"), Direction.AT_LEAST, True),
        (Decimal("2.7"), Decimal("2.7"), Direction.AT_LEAST, True),
        (Decimal("2.6"), Decimal("2.7"), Direction.AT_LEAST, False),
        (Decimal("0"), Decimal("2.7"), Direction.AT_LEAST, False),
        # at_most: met while the total stays under the target, boundary included
        (Decimal("150"), Decimal("200"), Direction.AT_MOST, True),
        (Decimal("200"), Decimal("200"), Direction.AT_MOST, True),
        (Decimal("201"), Decimal("200"), Direction.AT_MOST, False),
        (Decimal("0"), Decimal("200"), Direction.AT_MOST, True),
    ],
)
def test_is_target_met(total, target, direction, expected):
    assert is_target_met(total, target, direction) is expected
