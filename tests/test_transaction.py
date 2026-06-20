from datetime import date
import dataclasses
import pytest

from sage.domain.transaction import Transaction
from decimal import Decimal


def test_transaction_with_different_ids_not_equal():
    a = Transaction("a", date(2026, 6, 19), "abc", Decimal("5.50"))
    b = Transaction("b", date(2026, 6, 19), "abc", Decimal("5.50"))

    assert a != b
    assert len({a, b}) == 2


def test_transaction_is_immutable():
    tx = Transaction(
        id="a", date=date(2026, 6, 19), description="abc", amount=Decimal("5.50")
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        tx.amount = Decimal("10.00")


def test_identical_transactions_are_equal():
    a = Transaction(
        id="x", date=date(2026, 6, 19), description="abc", amount=Decimal("5.50")
    )
    b = Transaction(
        id="x", date=date(2026, 6, 19), description="abc", amount=Decimal("5.50")
    )
    assert a == b
    assert len({a, b}) == 1
