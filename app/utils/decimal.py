# app/utils/decimal.py
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation


def round_decimal(value: Decimal | float | str | None) -> Decimal:
    """
    Arrotonda un valore a due decimali usando ROUND_HALF_UP.

    Args:
        value: Valore da arrotondare (Decimal, float, str o None).

    Returns:
        Decimal: Valore arrotondato a due decimali, o 0.00 se non valido.
    """
    if value is None:
        return Decimal("0.00")
    try:
        return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (ValueError, TypeError, InvalidOperation):
        return Decimal("0.00")
