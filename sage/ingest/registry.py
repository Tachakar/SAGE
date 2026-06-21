from pathlib import Path

from sage.ingest.parsers.base import BankParser
from sage.ingest.parsers.mbank import MBankParser
from sage.ingest.parsers.millennium import MillenniumParser


def detect_parser(path: Path) -> BankParser:
    with open(path, "r", encoding="cp1250", errors="ignore") as f:
        header_chunk = f.read(1024).lower()

    if "mbank" in header_chunk:
        return MBankParser()
    return MillenniumParser()
