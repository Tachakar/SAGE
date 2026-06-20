from decimal import Decimal, InvalidOperation


def parse_amount(raw: str) -> Decimal:
    cleaned = raw.strip()
    cleaned = cleaned.replace("\xa0", "").replace(" ", "")
    cleaned = cleaned.replace(",", ".")
    try:
        return Decimal(cleaned)
    except InvalidOperation as exc:
        raise ValueError(f"not a valid amount: {raw!r}") from exc


def format_amount(amount: Decimal) -> str:
    return f"{amount:.2f}".replace(".", ",")
