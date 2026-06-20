from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class Transaction:
    id: str
    date: date
    description: str
    amount: Decimal
