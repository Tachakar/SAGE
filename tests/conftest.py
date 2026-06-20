from datetime import date
from decimal import Decimal

from sage.domain.transaction import Transaction
from sage.domain.categorization import CategorizationResult, CategorizedTransaction

DEFAULT_DATE = date(2026, 6, 19)


def make_tx(
    description: str = "abc", amount: str = "100.00", date: date = DEFAULT_DATE
) -> Transaction:
    return Transaction(
        id="t1", date=date, description=description, amount=Decimal(amount)
    )


def make_categorized(
    description: str = "abc",
    amount: str = "10.00",
    date: date = DEFAULT_DATE,
    category: str = "Food",
    rule_name: str | None = "food",
) -> CategorizedTransaction:
    return CategorizedTransaction(
        make_tx(description, amount, date),
        result=CategorizationResult(category=category, rule_name=rule_name),
    )
