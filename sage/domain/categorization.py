from dataclasses import dataclass

from sage.domain.transaction import Transaction


@dataclass(frozen=True)
class CategorizationResult:
    category: str
    rule_name: str | None


@dataclass(frozen=True)
class CategorizedTransaction:
    tx: Transaction
    result: CategorizationResult
