import csv
import datetime
from pathlib import Path
from typing import Iterator

from sage.domain.money import parse_amount
from sage.domain.transaction import Transaction
from sage.ingest.parsers.base import BankParser


class PkoParser(BankParser):
    def parse(self, path: Path) -> Iterator[Transaction]:
        with open(path, "r", encoding="cp1250", errors="replace") as f:
            reader = csv.reader(f)
            
            for row in reader:
                if row and row[0].strip() == "Data operacji":
                    break
                    
            for i, row in enumerate(reader):
                if len(row) < 7:
                    continue
                    
                date_str = row[0].strip()
                tx_type = row[2].strip()
                amount_str = row[3].strip()
                
                desc_parts = [tx_type] + [p.strip() for p in row[6:] if p.strip()]
                description = " | ".join(desc_parts)
                
                try:
                    date = datetime.date.fromisoformat(date_str)
                    amount = parse_amount(amount_str)
                    tx_id = f"pko_{i}"
                    yield Transaction(
                        id=tx_id,
                        date=date,
                        amount=amount,
                        description=description
                    )
                except Exception:
                    continue
