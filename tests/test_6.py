import pytest
from definition_87271713ae7b4bd39730eae6a4a40fe4 import calculate_eve

@pytest.mark.parametrize("pv_assets, pv_liabilities, expected", [
    (1000.0, 500.0, 500.0),            # Standard case: Assets greater than liabilities
    (750.0, 750.0, 0.0),               # Edge case: Assets equal to liabilities (EVE is zero)
    (200.0, 300.0, -100.0),            # Edge case: Assets less than liabilities (Negative EVE)
    (0.0, 150.0, -150.0),              # Edge case: Zero assets
    (500.0, "invalid_value", TypeError), # Edge case: Invalid type for liability
])
def test_calculate_eve(pv_assets, pv_liabilities, expected):
    try:
        # Use pytest.approx for floating-point comparisons to avoid precision issues
        assert calculate_eve(pv_assets, pv_liabilities) == pytest.approx(expected)
    except Exception as e:
        # This block catches expected exceptions for invalid inputs
        assert isinstance(e, expected)