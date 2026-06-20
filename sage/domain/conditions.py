from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Callable, override

from sage.domain.transaction import Transaction


class Condition(ABC):
    @abstractmethod
    def evaluate(self, tx: Transaction) -> bool: ...

    def __and__(self, other: Condition) -> And:
        return And(self, other)

    def __or__(self, other: Condition) -> Or:
        return Or(self, other)

    def __invert__(self) -> Not:
        return Not(self)


@dataclass(frozen=True)
class Contains(Condition):
    text: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "text", self.text.strip())

    @override
    def evaluate(self, tx: Transaction) -> bool:
        return self.text.lower() in tx.description.lower()


@dataclass(frozen=True)
class Amount(Condition):
    op: Callable[[Decimal, Decimal], bool]
    threshold: Decimal

    @override
    def evaluate(self, tx: Transaction) -> bool:
        return self.op(tx.amount, self.threshold)


@dataclass(frozen=True)
class BinaryCondition(Condition, ABC):
    left: Condition
    right: Condition


class And(BinaryCondition):
    @override
    def evaluate(self, tx: Transaction) -> bool:
        return self.left.evaluate(tx) and self.right.evaluate(tx)


class Or(BinaryCondition):
    @override
    def evaluate(self, tx: Transaction) -> bool:
        return self.left.evaluate(tx) or self.right.evaluate(tx)


@dataclass(frozen=True)
class Not(Condition):
    condition: Condition

    @override
    def evaluate(self, tx: Transaction) -> bool:
        return not self.condition.evaluate(tx)
