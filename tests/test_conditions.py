from datetime import date
from decimal import Decimal
import operator
from typing import Callable

import pytest

from sage.domain.conditions import Amount, And, Condition, Contains, Not, Or
from sage.domain.transaction import Transaction


def make_tx(description: str = "abc", amount: str = "100.00") -> Transaction:
    return Transaction(
        id="t1", date=date(2026, 6, 19), description=description, amount=Decimal(amount)
    )


CONTAINS_CASES: list[tuple[str, str, bool]] = [
    ("Sklep Biedronka", "Biedronka", True),
    ("Sklep biedronka", "Biedronka", True),
    ("Sklep Biedronka", "Lidl", False),
    ("Transakcja BLIK", "bLiK  ", True),
]

AMOUNT_CASES: list[tuple[Callable[[Decimal, Decimal], bool], Decimal, str, bool]] = [
    (operator.gt, Decimal("-100"), "-1.5", True),
    (operator.gt, Decimal("50"), "0.25", False),
    (operator.lt, Decimal("50"), "0.25", True),
    (operator.eq, Decimal("25"), "25.00", True),
]


@pytest.mark.parametrize("description, text, expected", CONTAINS_CASES)
def test_contains(description: str, text: str, expected: bool) -> None:
    tx = make_tx(description=description)
    assert Contains(text).evaluate(tx) == expected


@pytest.mark.parametrize("op, threshold, tx_amount, expected", AMOUNT_CASES)
def test_amount(
    op: Callable[[Decimal, Decimal], bool],
    threshold: Decimal,
    tx_amount: str,
    expected: bool,
) -> None:
    tx = make_tx(amount=tx_amount)
    assert Amount(op, Decimal(threshold)).evaluate(tx) == expected


AND_CASES: list[tuple[Condition, Condition, str, str, bool]] = [
    (
        Contains("biedronka"),
        Amount(operator.lt, Decimal("0")),
        "Sklep Biedronka",
        "-12.50",
        True,
    ),
    (
        Contains("lidl"),
        Amount(operator.lt, Decimal("0")),
        "Sklep Biedronka",
        "-12.50",
        False,
    ),
    (
        Contains("biedronka"),
        Amount(operator.gt, Decimal("0")),
        "Sklep Biedronka",
        "-12.50",
        False,
    ),
]

OR_CASES: list[tuple[Condition, Condition, str, str, bool]] = [
    (
        Contains("lidl"),
        Amount(operator.lt, Decimal("0")),
        "Sklep Biedronka",
        "-12.50",
        True,
    ),
    (
        Contains("biedronka"),
        Amount(operator.gt, Decimal("0")),
        "Sklep Biedronka",
        "-12.50",
        True,
    ),
    (
        Contains("lidl"),
        Amount(operator.gt, Decimal("0")),
        "Sklep Biedronka",
        "-12.50",
        False,
    ),
]

NOT_CASES: list[tuple[Condition, str, str, bool]] = [
    (Contains("biedronka"), "Sklep Biedronka", "-12.50", False),
    (Contains("lidl"), "Sklep Biedronka", "-12.50", True),
]


@pytest.mark.parametrize("left, right, description, amount, expected", AND_CASES)
def test_and(
    left: Condition,
    right: Condition,
    description: str,
    amount: str,
    expected: bool,
) -> None:
    tx = make_tx(description=description, amount=amount)
    assert And(left, right).evaluate(tx) == expected


@pytest.mark.parametrize("left, right, description, amount, expected", OR_CASES)
def test_or(
    left: Condition,
    right: Condition,
    description: str,
    amount: str,
    expected: bool,
) -> None:
    tx = make_tx(description=description, amount=amount)
    assert Or(left, right).evaluate(tx) == expected


@pytest.mark.parametrize("condition, description, amount, expected", NOT_CASES)
def test_not(
    condition: Condition, description: str, amount: str, expected: bool
) -> None:
    tx = make_tx(description=description, amount=amount)
    assert Not(condition).evaluate(tx) == expected


def test_nested_composite() -> None:
    condition = And(
        Or(Contains("lidl"), Contains("biedronka")),
        Amount(operator.lt, Decimal("0")),
    )
    tx = make_tx(description="Sklep Biedronka", amount="-12.50")
    assert condition.evaluate(tx) is True
