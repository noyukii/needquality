from decimal import Decimal, InvalidOperation


class MoneyError(ValueError):
    pass


def parse_money(raw: str) -> Decimal:
    text = raw.strip().replace(",", "")
    if text.startswith("$"):
        text = text[1:]
    try:
        value = Decimal(text)
    except InvalidOperation as exc:
        raise MoneyError(f"invalid amount: {raw!r}") from exc
    if value.as_tuple().exponent < -2:
        raise MoneyError(f"too many decimal places: {raw!r}")
    return value
