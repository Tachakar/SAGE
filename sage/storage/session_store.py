import json
from pathlib import Path
from typing import Optional, TypedDict


class SessionDict(TypedDict):
    csv_path: str
    bank: str
    search_query: str
    rule_filter: Optional[str]
    browse_page: int
    budget: Optional[str]


def load_session(path: Path) -> Optional[SessionDict]:
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def save_session(session: SessionDict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(session, f, indent=2)
