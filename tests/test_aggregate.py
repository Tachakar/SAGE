from datetime import date
from decimal import Decimal

import pytest

from sage.engine.categorizer import CategorizedTransaction
from sage.reports.aggregate import by_month, group_by_category
from tests.conftest import make_categorized

GROUP_BY_CATEGORY_CASES = [
    (
        [
            make_categorized(amount="10.00", category="Food"),
            make_categorized(amount="20.00", category="Food"),
            make_categorized(amount="30.00", category="Food"),
        ],
        {"Food": Decimal("60.00")},
    ),
    (
        [
            make_categorized(amount="10.00", category="Food"),
            make_categorized(amount="5.00", category="Transport"),
        ],
        {"Food": Decimal("10.00"), "Transport": Decimal("5.00")},
    ),
    ([], {}),
]

BY_MONTH_CASES = [
    (
        [
            make_categorized(amount="10.00", date=date(2026, 6, 1)),
            make_categorized(amount="20.00", date=date(2026, 6, 15)),
            make_categorized(amount="30.00", date=date(2026, 6, 30)),
        ],
        {(2026, 6): Decimal("60.00")},
    ),
    (
        [
            make_categorized(amount="10.00", date=date(2025, 6, 1)),
            make_categorized(amount="5.00", date=date(2026, 6, 1)),
        ],
        {(2025, 6): Decimal("10.00"), (2026, 6): Decimal("5.00")},
    ),
    ([], {}),
]


@pytest.mark.parametrize("rows, expected", GROUP_BY_CATEGORY_CASES)
def test_group_by_category(
    rows: list[CategorizedTransaction], expected: dict[str, Decimal]
) -> None:
    assert group_by_category(rows) == expected


@pytest.mark.parametrize("rows, expected", BY_MONTH_CASES)
def test_by_month(
    rows: list[CategorizedTransaction], expected: dict[tuple[int, int], Decimal]
) -> None:
    assert by_month(rows) == expected
