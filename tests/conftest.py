from datetime import date
from decimal import Decimal

from sage.domain.transaction import Transaction


def make_tx(description: str = "abc", amount: str = "100.00") -> Transaction:
    return Transaction(
        id="t1", date=date(2026, 6, 19), description=description, amount=Decimal(amount)
    )
