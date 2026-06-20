from abc import ABC, abstractmethod
from collections.abc import Iterator
from pathlib import Path

from sage.domain.transaction import Transaction


class BankParser(ABC):
    @abstractmethod
    def parse(self, path: Path) -> Iterator[Transaction]: ...
