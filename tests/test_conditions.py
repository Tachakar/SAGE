from datetime import date
from decimal import Decimal
import operator
from typing import Callable

import pytest

from sage.domain.conditions import Amount, Contains
from sage.domain.transaction import Transaction


def make_tx(description: str = "abc", amount: str = "100.00") -> Transaction:
    return Transaction(
        id="t1", date=date(2026, 6, 19), description=description, amount=Decimal(amount)
    )


@pytest.mark.parametrize(
    "description, text, expected",
    [
        ("Sklep Biedronka", "Biedronka", True),
        ("Sklep biedronka", "Biedronka", True),
        ("Sklep Biedronka", "Lidl", False),
        ("Transakcja BLIK", "bLiK  ", True),
    ],
)
def test_contains(description: str, text: str, expected: bool):
    tx = make_tx(description=description)
    assert Contains(text).evaluate(tx) == expected


@pytest.mark.parametrize(
    "op, threshold, tx_amount, expected",
    [
        (operator.gt, Decimal("-100"), "-1.5", True),
        (operator.gt, Decimal("50"), "0.25", False),
        (operator.lt, Decimal("50"), "0.25", True),
        (operator.eq, Decimal("25"), "25.00", True),
    ],
)
def test_amount(
    op: Callable[[Decimal, Decimal], bool],
    threshold: Decimal,
    tx_amount: str,
    expected: bool,
):
    tx = make_tx(amount=tx_amount)
    assert Amount(op, Decimal(threshold)).evaluate(tx) == expected
