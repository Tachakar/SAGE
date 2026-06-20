from dataclasses import dataclass
from typing import Callable

from sage.domain.rule import Rule
from sage.domain.transaction import Transaction

UNCATEGORIZED = "Uncategorized"


@dataclass(frozen=True)
class CategorizationResult:
    category: str
    rule_name: str | None


@dataclass(frozen=True)
class CategorizedTransaction:
    tx: Transaction
    result: CategorizationResult


def make_categorizer(
    rules: list[Rule],
) -> Callable[[Transaction], CategorizationResult]:
    sorted_rules = sorted(rules, key=lambda rule: rule.priority)

    def categorize(tx: Transaction) -> CategorizationResult:
        for rule in sorted_rules:
            if rule.condition.evaluate(tx):
                return CategorizationResult(category=rule.category, rule_name=rule.name)
        return CategorizationResult(category=UNCATEGORIZED, rule_name=None)

    return categorize
