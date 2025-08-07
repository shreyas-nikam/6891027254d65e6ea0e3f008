import pytest
from definition_8257a8c369334619bddae42c90b06aa9 import calculate_delta_eve

@pytest.mark.parametrize("baseline_eve, shocked_eve, expected", [
    (100.0, 120.0, 20.0),      # Standard case: positive Delta EVE
    (150.0, 100.0, -50.0),     # Standard case: negative Delta EVE
    (75.5, 75.5, 0.0),         # Edge case: zero Delta EVE (no change)
    (0.0, 10.5, 10.5),         # Edge case: baseline EVE is zero
    ("abc", 50.0, TypeError),  # Edge case: invalid type for baseline_eve
])
def test_calculate_delta_eve(baseline_eve, shocked_eve, expected):
    try:
        result = calculate_delta_eve(baseline_eve, shocked_eve)
        # Use pytest.approx for robust floating-point comparisons
        assert result == pytest.approx(expected)
    except Exception as e:
        # Assert that the caught exception is of the expected type
        assert isinstance(e, expected)

