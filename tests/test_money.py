from decimal import Decimal

import pytest

from sage.domain.money import parse_amount, format_amount

PARSE_AMOUNT_VALID_CASES = [
    ("1 234,56", Decimal("1234.56")),
    ("-12,50", Decimal("-12.50")),
    ("0,00", Decimal("0.00")),
    ("1\xa0234,56", Decimal("1234.56")),
    ("12,5", Decimal("12.5")),
    ("  1234,56  ", Decimal("1234.56")),
    ("+123,45", Decimal("123.45")),
    ("12 345 678,90", Decimal("12345678.90")),
    ("-12 345,67", Decimal("-12345.67")),
    ("  -1234,56  ", Decimal("-1234.56")),
]

PARSE_AMOUNT_INVALID_CASES = ["abc", "", "   "]

FORMAT_AMOUNT_CASES = [
    (Decimal("1234.50"), "1234,50"),
    (Decimal("-12.50"), "-12,50"),
    (Decimal("0"), "0,00"),
    (Decimal("12.5"), "12,50"),
]


@pytest.mark.parametrize("raw, expected", PARSE_AMOUNT_VALID_CASES)
def test_parse_amount(raw, expected):
    assert parse_amount(raw) == expected


@pytest.mark.parametrize("raw", PARSE_AMOUNT_INVALID_CASES)
def test_parse_amount_invalid_raises_value_error(raw):
    with pytest.raises(ValueError):
        parse_amount(raw)


@pytest.mark.parametrize("amount, expected", FORMAT_AMOUNT_CASES)
def test_format_amount(amount, expected):
    assert format_amount(amount) == expected


def test_format_amount_round_trip():
    original = "1234,56"
    assert format_amount(parse_amount(original)) == original
