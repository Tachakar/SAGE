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


class BinaryCondition(Condition, ABC):
    def __init__(self, left: Condition, right: Condition) -> None:
        super().__init__()
        self.left: Condition = left
        self.right: Condition = right


class And(BinaryCondition):
    @override
    def evaluate(self, tx: Transaction) -> bool:
        return self.left.evaluate(tx) and self.right.evaluate(tx)


class Or(BinaryCondition):
    @override
    def evaluate(self, tx: Transaction) -> bool:
        return self.left.evaluate(tx) or self.right.evaluate(tx)


class Not(Condition):
    def __init__(self, condition: Condition) -> None:
        super().__init__()
        self.condition: Condition = condition

    @override
    def evaluate(self, tx: Transaction) -> bool:
        return not self.condition.evaluate(tx)
