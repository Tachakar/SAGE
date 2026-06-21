from sage.ingest.parsers.base import BankParser
from sage.ingest.parsers.mbank import MBankParser
from sage.ingest.parsers.millennium import MillenniumParser
from sage.ingest.parsers.pko import PkoParser

SUPPORTED_PARSER: dict[str, type[BankParser]] = {
    "Millennium": MillenniumParser,
    "mBank": MBankParser,
    "PKO": PkoParser,
}


def detect_parser(name: str) -> BankParser:
    parser = SUPPORTED_PARSER.get(name)
    if parser is None:
        raise ValueError(f"unknown bank: {name!r}")
    return parser()
