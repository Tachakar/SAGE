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
        with open(path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f, delimiter=",")
            for row_number, row in enumerate(reader, start=1):
                debit, credit = row["Obciążenia"], row["Uznania"]
                if debit and credit:
                    raise ValueError(f"row {row_number}: both debit and credit set in {row!r}")
                raw_amount = debit or credit
                if not raw_amount:
                    raise ValueError(f"row {row_number}: no amount in {row!r}")
                try:
                    amount = parse_amount(raw_amount)
                except ValueError as exc:
                    raise ValueError(f"row {row_number}: {exc}") from exc
                yield Transaction(
                    id=f"{path.name}:{row_number}",
                    date=date.fromisoformat(row["Data transakcji"]),
                    description=f"{row['Odbiorca/Zleceniodawca']} {row['Opis']}".strip(),
                    amount=amount,
                )
