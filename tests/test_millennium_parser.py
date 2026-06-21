from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from sage.domain.transaction import Transaction
from sage.ingest.parsers.millennium import MillenniumParser

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "millennium_sample.csv"

HEADER = "Numer rachunku/karty,Data transakcji,Data rozliczenia,Rodzaj transakcji,Na konto/Z konta,Odbiorca/Zleceniodawca,Opis,Obciążenia,Uznania,Saldo,Waluta"


def write_csv(tmp_path: Path, row: str) -> Path:
    path = tmp_path / "broken.csv"
    path.write_text(HEADER + "\n" + row + "\n", encoding="utf-8-sig")
    return path


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


def test_millennium_parser_rejects_both_debit_and_credit_set(tmp_path: Path) -> None:
    row = "PL00,2026-06-15,2026-06-15,BLIK,123,JOHN DOE,Sklep,-12.50,10.00,1000.00,PLN"
    path = write_csv(tmp_path, row)
    parser = MillenniumParser()

    with pytest.raises(ValueError, match="row 1.*both debit and credit"):
        list(parser.parse(path))


def test_millennium_parser_rejects_missing_amount(tmp_path: Path) -> None:
    row = "PL00,2026-06-15,2026-06-15,BLIK,123,JOHN DOE,Sklep,,,1000.00,PLN"
    path = write_csv(tmp_path, row)
    parser = MillenniumParser()

    with pytest.raises(ValueError, match="row 1.*no amount"):
        list(parser.parse(path))


def test_millennium_parser_rejects_invalid_date(tmp_path: Path) -> None:
    row = "PL00,not-a-date,2026-06-15,BLIK,123,JOHN DOE,Sklep,-12.50,,1000.00,PLN"
    path = write_csv(tmp_path, row)
    parser = MillenniumParser()

    with pytest.raises(ValueError, match="row 1.*invalid date"):
        list(parser.parse(path))


def test_millennium_parser_rejects_missing_column(tmp_path: Path) -> None:
    path = tmp_path / "broken.csv"
    path.write_text("Data transakcji,Opis\n2026-06-15,Sklep\n", encoding="utf-8-sig")
    parser = MillenniumParser()

    with pytest.raises(ValueError, match="row 1.*missing column"):
        list(parser.parse(path))
