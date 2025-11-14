# app/tests/utils/test_decimal.py

from decimal import Decimal
import pytest

from app.utils import decimal as decimal_utils


@pytest.mark.parametrize(
    "input_value, expected",
    [
        (None, Decimal("0.00")),
        (Decimal("1.234"), Decimal("1.23")),
        (Decimal("1.235"), Decimal("1.24")),
        (1.234, Decimal("1.23")),
        (1.235, Decimal("1.24")),
        ("1.234", Decimal("1.23")),
        ("1.235", Decimal("1.24")),
        ("abc", Decimal("0.00")),  # invalid string input
        ("", Decimal("0.00")),  # empty string
        ([], Decimal("0.00")),  # invalid type
    ],
)
def test_round_decimal(input_value, expected):
    assert decimal_utils.round_decimal(input_value) == expected
