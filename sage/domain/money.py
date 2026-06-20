from decimal import Decimal, InvalidOperation

def parse_amount(raw: str) -> Decimal:
    cleaned = raw.strip()
    cleaned = cleaned.replace("\xa0","").replace(" ", "")
    cleaned = cleaned.replace(",",".")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        raise ValueError(f"not a valid amount: {raw!r}")
