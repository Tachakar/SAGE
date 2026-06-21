import pytest

from sage.ingest.parsers.mbank import MBankParser
from sage.ingest.parsers.millennium import MillenniumParser
from sage.ingest.registry import detect_parser


def test_detect_parser_returns_millennium_parser() -> None:
    assert isinstance(detect_parser("Millennium"), MillenniumParser)


def test_detect_parser_returns_mbank_parser() -> None:
    assert isinstance(detect_parser("mBank"), MBankParser)


def test_detect_parser_unknown_bank_raises_value_error() -> None:
    with pytest.raises(ValueError, match="unknown bank"):
        detect_parser("RaiffeisenPolbank")


def test_detect_parser_returns_new_instance_each_call() -> None:
    assert detect_parser("Millennium") is not detect_parser("Millennium")
