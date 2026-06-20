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
]


@pytest.mark.parametrize("condition, tx", SERIALIZATION_CASES)
def test_round_trip_preserves_evaluation(condition: Condition, tx: Transaction) -> None:
    rebuilt = from_dict(to_dict(condition))
    assert rebuilt.evaluate(tx) == condition.evaluate(tx)


@pytest.mark.parametrize("condition, tx", SERIALIZATION_CASES)
def test_to_dict_is_json_serializable(condition: Condition, tx: Transaction) -> None:
    json.dumps(to_dict(condition))
