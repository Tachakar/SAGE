import datetime
from pathlib import Path
from typing import Iterator

from sage.domain.money import parse_amount
from sage.domain.transaction import Transaction
from sage.ingest.parsers.base import BankParser


class MBankParser(BankParser):
    def parse(self, path: Path) -> Iterator[Transaction]:
        with open(path, "r", encoding="cp1250", errors="replace") as f:
            lines = f.readlines()
            
        start_idx = 0
        for i, line in enumerate(lines):
            if line.startswith("#Data ksi"):
                start_idx = i + 1
                break
                
        for i in range(start_idx, len(lines)):
            line = lines[i].strip()
            if not line or line.startswith(";"):
                continue
            if line.startswith("#Saldo") or line.startswith("Niniejszy"):
                continue
                
            parts = line.split(";")
            if len(parts) < 8:
                continue
                
            date_str = parts[0]
            description = parts[3].strip('"')
            amount_str = parts[6]
            
            try:
                date = datetime.date.fromisoformat(date_str)
                amount = parse_amount(amount_str)
                tx_id = f"mbank_{i}"
                yield Transaction(
                    id=tx_id,
                    date=date,
                    amount=amount,
                    description=description
                )
            except Exception:
                continue
