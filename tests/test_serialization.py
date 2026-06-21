import json
import operator
from decimal import Decimal

import pytest

from sage.domain.conditions import Amount, And, Condition, Contains, Not, Or
from sage.domain.transaction import Transaction
from sage.storage.serialization import from_dict, to_dict
from tests.conftest import make_tx

SERIALIZATION_CASES: list[tuple[Condition, Transaction]] = [
    (Contains("biedronka"), make_tx(description="Sklep Biedronka")),
    (Amount(operator.lt, Decimal("0")), make_tx(amount="-12.50")),
    (
        And(Contains("biedronka"), Amount(operator.lt, Decimal("0"))),
        make_tx(description="Sklep Biedronka", amount="-12.50"),
    ),
    (
        Or(Contains("biedronka"), Contains("lidl")),
        make_tx(description="Sklep Lidl"),
    ),
    (Not(Contains("biedronka")), make_tx(description="Apteka")),
    (
        And(
            Or(Contains("lidl"), Contains("biedronka")),
            Amount(operator.lt, Decimal("0")),
        ),
        make_tx(description="Sklep Biedronka", amount="-12.50"),
    ),
    (Amount(operator.gt, Decimal("100"), absolute=True), make_tx(amount="-150.00")),
]


@pytest.mark.parametrize("condition, tx", SERIALIZATION_CASES)
def test_round_trip_preserves_evaluation(condition: Condition, tx: Transaction) -> None:
    rebuilt = from_dict(to_dict(condition))
    assert rebuilt.evaluate(tx) == condition.evaluate(tx)


@pytest.mark.parametrize("condition, tx", SERIALIZATION_CASES)
def test_to_dict_is_json_serializable(condition: Condition, tx: Transaction) -> None:
    json.dumps(to_dict(condition))


def test_to_dict_preserves_absolute_flag() -> None:
    data = to_dict(Amount(operator.gt, Decimal("100"), absolute=True))
    assert data["absolute"] is True
    rebuilt = from_dict(data)
    assert rebuilt == Amount(operator.gt, Decimal("100"), absolute=True)


def test_from_dict_defaults_absolute_to_false_when_missing() -> None:
    rebuilt = from_dict({"type": "amount", "op": "gt", "threshold": "100"})
    assert rebuilt == Amount(operator.gt, Decimal("100"), absolute=False)


def test_to_dict_unsupported_operator_raises_value_error() -> None:
    with pytest.raises(ValueError, match="unsupported operator"):
        to_dict(Amount(lambda a, b: True, Decimal("0")))


def test_to_dict_unknown_condition_type_raises_value_error() -> None:
    class FakeCondition(Condition):
        def evaluate(self, tx: Transaction) -> bool:
            return True

    with pytest.raises(ValueError, match="unknown condition type"):
        to_dict(FakeCondition())


def test_from_dict_unknown_operator_raises_value_error() -> None:
    with pytest.raises(ValueError, match="unknown operator"):
        from_dict({"type": "amount", "op": "bogus", "threshold": "100"})


def test_from_dict_invalid_threshold_raises_value_error() -> None:
    with pytest.raises(ValueError, match="invalid amount threshold"):
        from_dict({"type": "amount", "op": "gt", "threshold": "not-a-number"})


def test_from_dict_unknown_condition_dict_raises_value_error() -> None:
    with pytest.raises(ValueError, match="unknown condition dict"):
        from_dict({"type": "bogus"})
