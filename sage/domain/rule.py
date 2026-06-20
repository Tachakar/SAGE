from dataclasses import dataclass

from sage.domain.conditions import Condition


@dataclass(frozen=True)
class Rule:
    name: str
    condition: Condition
    category: str
    priority: int  # lower priority = more important
