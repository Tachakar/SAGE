import json
from pathlib import Path

from sage.domain.rule import Rule
from sage.storage.serialization import from_dict, to_dict


def load_rules(path: Path) -> list[Rule]:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    rules = []
    for d in data:
        rules.append(Rule(
            name=d["name"],
            condition=from_dict(d["condition"]),
            category=d["category"],
            priority=d["priority"],
        ))
    return rules


def save_rules(rules: list[Rule], path: Path) -> None:
    data = []
    for r in rules:
        data.append({
            "name": r.name,
            "condition": to_dict(r.condition),
            "category": r.category,
            "priority": r.priority,
        })
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
