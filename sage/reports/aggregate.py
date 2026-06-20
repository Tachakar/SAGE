from collections import defaultdict
from decimal import Decimal

from sage.engine.categorizer import CategorizedTransaction


def group_by_category(rows: list[CategorizedTransaction]) -> dict[str, Decimal]:
    total: dict[str, Decimal] = defaultdict(Decimal)
    for row in rows:
        category = row.result.category
        total[category] += row.tx.amount
    return dict(total)


def by_month(rows: list[CategorizedTransaction]) -> dict[tuple[int, int], Decimal]:
    total: dict[tuple[int, int], Decimal] = defaultdict(Decimal)
    for row in rows:
        key = (row.tx.date.year, row.tx.date.month)
        total[key] += row.tx.amount
    return dict(total)
