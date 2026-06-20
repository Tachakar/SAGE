import operator
from decimal import Decimal

import pytest

from sage.domain.conditions import Amount, Contains
from sage.domain.rule import Rule
from sage.engine.categorizer import UNCATEGORIZED, make_categorizer
from tests.conftest import make_tx

RULES = [
    Rule("groceries", Contains("biedronka"), "Groceries", priority=1),
    Rule("debit", Amount(operator.lt, Decimal("0")), "Other debit", priority=2),
]

CATEGORIZE_CASES: list[tuple[str, str, str, str | None]] = [
    ("Sklep Biedronka", "-12.50", "Groceries", "groceries"),
    ("Apteka", "-5.00", "Other debit", "debit"),
    ("Wynagrodzenie", "3000.00", UNCATEGORIZED, None),
]


@pytest.mark.parametrize(
    "description, amount, expected_category, expected_rule_name", CATEGORIZE_CASES
)
def test_categorize(
    description: str, amount: str, expected_category: str, expected_rule_name: str
) -> None:
    categorize = make_categorizer(RULES)
    tx = make_tx(description=description, amount=amount)
    result = categorize(tx)
    assert result.category == expected_category
    assert result.rule_name == expected_rule_name


def test_priority_order_decides_ties() -> None:
    tx = make_tx(description="Sklep Biedronka", amount="-12.50")
    categorize = make_categorizer(RULES)
    result = categorize(tx)
    assert result.rule_name == "groceries"
    assert result.category == "Groceries"


def test_empty_rules_list_gives_uncategorized() -> None:
    categorize = make_categorizer([])
    tx = make_tx()
    result = categorize(tx)
    assert result.category == UNCATEGORIZED
    assert result.rule_name is None


def test_same_priority_keeps_list_order() -> None:
    rules = [
        Rule("first", Contains("biedronka"), "A", priority=1),
        Rule("second", Contains("biedronka"), "B", priority=1),
    ]
    categorize = make_categorizer(rules)
    tx = make_tx(description="Sklep Biedronka")
    result = categorize(tx)
    assert result.rule_name == "first"


def test_categorizer_is_independent_of_later_mutations_to_input_list() -> None:
    rules = [Rule("groceries", Contains("biedronka"), "Groceries", priority=1)]
    categorize = make_categorizer(rules)
    rules.append(
        Rule("debit", Amount(operator.lt, Decimal("0")), "Other debit", priority=0)
    )

    tx = make_tx(description="Sklep Biedronka", amount="-12.50")
    result = categorize(tx)
    assert result.rule_name == "groceries"
