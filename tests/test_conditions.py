import dataclasses
from decimal import Decimal
import operator
from typing import Callable

import pytest

from sage.domain.conditions import (
    Amount,
    And,
    Condition,
    Contains,
    Not,
    Or,
    all_of,
    any_of,
)
from tests.conftest import make_tx


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


def test_and_operator_builds_working_and() -> None:
    cond = Contains("biedronka") & Amount(operator.lt, Decimal("0"))
    assert isinstance(cond, And)
    assert cond.evaluate(make_tx(description="Sklep Biedronka", amount="-12.50"))
    assert not cond.evaluate(make_tx(description="Sklep Biedronka", amount="12.50"))


def test_or_operator_builds_working_or() -> None:
    cond = Contains("biedronka") | Contains("lidl")
    assert isinstance(cond, Or)
    assert cond.evaluate(make_tx(description="Sklep Biedronka"))
    assert cond.evaluate(make_tx(description="Sklep Lidl"))
    assert not cond.evaluate(make_tx(description="Apteka"))


def test_invert_operator_builds_working_not() -> None:
    cond = ~Contains("biedronka")
    assert isinstance(cond, Not)
    assert cond.evaluate(make_tx(description="Apteka"))
    assert not cond.evaluate(make_tx(description="Sklep Biedronka"))


def test_contains_is_immutable() -> None:
    cond = Contains("biedronka")
    with pytest.raises(dataclasses.FrozenInstanceError):
        cond.text = "lidl"


def test_and_is_immutable() -> None:
    cond = And(Contains("a"), Amount(operator.gt, Decimal("0")))
    with pytest.raises(dataclasses.FrozenInstanceError):
        cond.left = Contains("b")


def test_any_of_folds_into_or_tree() -> None:
    cond = any_of([Contains("biedronka"), Contains("lidl"), Contains("zabka")])
    assert isinstance(cond, Or)
    assert cond.evaluate(make_tx(description="Sklep Lidl"))
    assert cond.evaluate(make_tx(description="Zabka 123"))
    assert not cond.evaluate(make_tx(description="Apteka"))


def test_all_of_folds_into_and_tree() -> None:
    cond = all_of(
        [
            Contains("sklep"),
            Contains("biedronka"),
            Amount(operator.lt, Decimal("0")),
        ]
    )
    assert isinstance(cond, And)
    assert cond.evaluate(make_tx(description="Sklep Biedronka", amount="-12.50"))
    assert not cond.evaluate(make_tx(description="Sklep Biedronka", amount="12.50"))
    assert not cond.evaluate(make_tx(description="Sklep Lidl", amount="-12.50"))


def test_any_of_matches_manual_or_chain() -> None:
    conditions = [Contains("biedronka"), Contains("lidl"), Contains("zabka")]
    folded = any_of(conditions)
    manual = Contains("biedronka") | Contains("lidl") | Contains("zabka")
    for description in ("Sklep Lidl", "Zabka", "Biedronka", "Apteka"):
        tx = make_tx(description=description)
        assert folded.evaluate(tx) == manual.evaluate(tx)


def test_fold_of_single_condition_returns_it_unwrapped() -> None:
    only = Contains("lidl")
    assert any_of([only]) is only
    assert all_of([only]) is only


@pytest.mark.parametrize("fold", [any_of, all_of])
def test_fold_of_empty_raises_value_error(
    fold: Callable[[list[Condition]], Condition],
) -> None:
    with pytest.raises(ValueError):
        fold([])
