from decimal import Decimal

import pytest

from sage.domain.money import parse_amount


def test_parse_amount_with_thousands_separator():
    assert parse_amount("1 234,56") == Decimal("1234.56")


def test_parse_amount_negative():
    assert parse_amount("-12,50") == Decimal("-12.50")


def test_parse_amount_zero():
    assert parse_amount("0,00") == Decimal("0.00")


def test_parse_amount_non_breaking_space():
    assert parse_amount("1\xa0234,56") == Decimal("1234.56")


def test_parse_amount_invalid_raises_value_error():
    with pytest.raises(ValueError):
        _ = parse_amount("abc")
