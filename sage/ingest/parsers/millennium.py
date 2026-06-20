import csv
from datetime import date
from pathlib import Path
from collections.abc import Iterator
from typing import override

from sage.domain.money import parse_amount
from sage.domain.transaction import Transaction
from sage.ingest.parsers.base import BankParser


class MillenniumParser(BankParser):
    @override
    def parse(self, path: Path) -> Iterator[Transaction]:
        with open(path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=",")
            for row_number, row in enumerate(reader, start=1):
                yield Transaction(
                    id=f"{path.name}:{row_number}",
                    date=date.fromisoformat(row["Data transakcji"]),
                    description=f"{row['Odbiorca/Zleceniodawca']} {row['Opis']}",
                    amount=parse_amount(row["Obciążenia"] or row["Uznania"]),
                )
