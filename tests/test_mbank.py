from datetime import date
from decimal import Decimal
from pathlib import Path

from sage.domain.transaction import Transaction
from sage.ingest.parsers.mbank import MBankParser

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "mbank_sample.csv"


def test_millennium_parser_against_fixture() -> None:
    parser = MBankParser()
    txs = list(parser.parse(FIXTURE_PATH))

    assert len(txs) == 4

    assert txs[0] == Transaction(
        id="mbank_1",
        date=date(2026, 3, 1),
        description="PRZELEW ďż˝RODKďż˝W",
        amount=Decimal("-50.00"),
    )
    assert txs[1] == Transaction(
        id="mbank_2",
        date=date(2026, 3, 1),
        description="LIDL OBORNICKA     /Wroclaw                                           DATA TRANSAKCJI: 2026-02-28",
        amount=Decimal("-40.15"),
    )
    assert txs[2] == Transaction(
        id="mbank_3",
        date=date(2026, 3, 2),
        description="PRZELEW ďż˝RODKďż˝W",
        amount=Decimal("-6.50"),
    )
    assert txs[3] == Transaction(
        id="mbank_4",
        date=date(2026, 3, 2),
        description="ZA ZAKUPY",
        amount=Decimal("-167.00"),
    )
