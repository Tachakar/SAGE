from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Callable, override

from sage.domain.transaction import Transaction


class Condition(ABC):
    @abstractmethod
    def evaluate(self, tx: Transaction) -> bool: ...


class Contains(Condition):
    def __init__(self, text: str) -> None:
        super().__init__()
        self.text: str = text.strip()

    @override
    def evaluate(self, tx: Transaction) -> bool:
        return self.text.lower() in tx.description.lower()


class Amount(Condition):
    def __init__(
        self, op: Callable[[Decimal, Decimal], bool], threshold: Decimal
    ) -> None:
        super().__init__()
        self.op: Callable[[Decimal, Decimal], bool] = op
        self.threshold: Decimal = threshold

    @override
    def evaluate(self, tx: Transaction) -> bool:
        return self.op(tx.amount, self.threshold)
