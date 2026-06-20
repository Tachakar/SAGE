from datetime import date
from decimal import Decimal
from pathlib import Path

from sage.domain.transaction import Transaction
from sage.ingest.parsers.millennium import MillenniumParser

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "millennium_sample.csv"


def test_millennium_parser_against_fixture() -> None:
    parser = MillenniumParser()
    txs = list(parser.parse(FIXTURE_PATH))

    assert len(txs) == 3

    assert txs[0] == Transaction(
        id="millennium_sample.csv:1",
        date=date(2026, 6, 15),
        description="JOHN DOE Sklep Biedronka 123",
        amount=Decimal("-12.50"),
    )
    assert txs[1] == Transaction(
        id="millennium_sample.csv:2",
        date=date(2026, 6, 16),
        description="Pracodawca SA Wynagrodzenie czerwiec",
        amount=Decimal("3000.00"),
    )
    assert txs[2] == Transaction(
        id="millennium_sample.csv:3",
        date=date(2026, 6, 17),
        description="APTEKA XYZ Platnosc kartą",
        amount=Decimal("-45.99"),
    )
