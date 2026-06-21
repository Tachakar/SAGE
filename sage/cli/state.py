from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import List, Optional

from sage.domain.categorization import CategorizedTransaction
from sage.domain.rule import Rule


@dataclass
class AppState:
    default_rules: List[Rule] = field(default_factory=list)
    user_rules: List[Rule] = field(default_factory=list)
    transactions: List[CategorizedTransaction] = field(default_factory=list)
    default_rules_path: Path = Path("data/default_rules.json")
    user_rules_path: Path = Path("data/user_rules.json")
    
    @property
    def rules(self) -> List[Rule]:
        return sorted(self.default_rules + self.user_rules, key=lambda r: r.priority)
    
    browse_page: int = 0
    search_query: str = ""
    rule_filter: Optional[str] = None
    last_csv_path: Optional[str] = None
    last_bank: Optional[str] = None
    budget: Optional[Decimal] = None
    
    def get_filtered_transactions(self) -> List[CategorizedTransaction]:
        filtered = []
        for tx_cat in self.transactions:
            desc = tx_cat.tx.description.lower()
            cat = tx_cat.result.category.lower()
            rule_name = tx_cat.result.rule_name or "-"
            
            if self.rule_filter and rule_name != self.rule_filter:
                continue
            if self.search_query and self.search_query not in desc and self.search_query not in cat:
                continue
            filtered.append(tx_cat)
        return filtered
