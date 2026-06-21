from datetime import date
from decimal import Decimal
from pathlib import Path

from sage.domain.transaction import Transaction
from sage.ingest.parsers.pko import PkoParser

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "pko_sample.csv"

def test_pko_parser_against_fixture() -> None:
    parser = PkoParser()
    txs = list(parser.parse(FIXTURE_PATH))

    assert len(txs) == 3

    assert txs[0] == Transaction(
        id="pko_0",
        date=date(2026, 6, 18),
        description="Płatność web - kod mobilny | Tytuł: 00000094292639249 | Numer telefonu: 48512015501 | Lokalizacja: Adres: www.koleo.pl | 'Operacja: 00000094292639249 | Numer referencyjny: 00000094292639249",
        amount=Decimal("-10.04"),
    )
    assert txs[1] == Transaction(
        id="pko_1",
        date=date(2026, 6, 13),
        description="Przelew na telefon przychodz. zew. | Rachunek odbiorcy: 37 1140 2004 0000 3002 8166 8200 | Nazwa odbiorcy: FILIP | Tytuł: PRZELEW NA TELEFON  OD: 48512015501 DO: 485*****038",
        amount=Decimal("-30.00"),
    )
    assert txs[2] == Transaction(
        id="pko_2",
        date=date(2026, 6, 8),
        description="Płatność web - kod mobilny | Tytuł: 00000094211450969 | Numer telefonu: 48512015501 | Lokalizacja: Adres: www.ebeactive.pl | 'Operacja: 00000094211450969 | Numer referencyjny: 00000094211450969",
        amount=Decimal("-139.00"),
    )
