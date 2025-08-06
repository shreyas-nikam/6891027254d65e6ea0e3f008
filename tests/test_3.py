import pytest
import pandas as pd
from definition_1b02ae0d54544635b960723651e0316f import generate_yield_curve # This assumes generate_yield_curve is directly importable, e.g., a static method or a top-level function.

# Define sample base curves for testing
base_curve_simple = pd.Series([0.01, 0.015, 0.02], index=[1, 5, 10], name='Rates') # Example: rates for 1Y, 5Y, 10Y tenors
base_curve_other = pd.Series([0.03, 0.035, 0.04], index=[0.5, 2, 7], name='Rates') # Example: rates for 0.5Y, 2Y, 7Y tenors

@pytest.mark.parametrize(
    "base_curve, shock_type, shock_magnitude, expected_output_or_exception",
    [
        # Test Case 1: Parallel Up Shock (Expected functionality)
        # Applies a positive uniform shift to all rates in the base curve.
        (base_curve_simple, 'Parallel Up', 0.005, pd.Series([0.015, 0.020, 0.025], index=[1, 5, 10], name='Rates')),

        # Test Case 2: Parallel Down Shock (Expected functionality)
        # Applies a negative uniform shift to all rates in the base curve.
        (base_curve_other, 'Parallel Down', 0.002, pd.Series([0.028, 0.033, 0.038], index=[0.5, 2, 7], name='Rates')),

        # Test Case 3: Zero Shock Magnitude (Edge Case)
        # If the shock magnitude is zero, the output curve should be identical to the input base curve.
        (base_curve_simple, 'Parallel Up', 0.0, base_curve_simple),

        # Test Case 4: Invalid Shock Type (Edge Case)
        # The function should raise a ValueError for an unrecognized shock type string.
        (base_curve_simple, 'Invalid Shock Type', 0.001, ValueError),

        # Test Case 5: Non-numeric Shock Magnitude (Edge Case)
        # Passing a non-float value for shock_magnitude should result in a TypeError.
        (base_curve_simple, 'Parallel Up', '0.001', TypeError), 
    ]
)
def test_generate_yield_curve(base_curve, shock_type, shock_magnitude, expected_output_or_exception):
    try:
        # Call the generate_yield_curve function.
        # Assuming `self` argument is either ignored for testing, or it's a static method,
        # or it's implicitly mocked by the test setup given the direct import instruction.
        # We pass None for 'self' as a placeholder.
        result = generate_yield_curve(None, base_curve, shock_type, shock_magnitude)

        # If an exception was expected, but no exception was raised, fail the test.
        if isinstance(expected_output_or_exception, type) and issubclass(expected_output_or_exception, Exception):
            pytest.fail(f"Expected {expected_output_or_exception.__name__} but no exception was raised. Got: {result}")
        else:
            # For pandas Series, use pd.testing.assert_series_equal for robust comparison
            pd.testing.assert_series_equal(result, expected_output_or_exception, check_dtype=True)

    except Exception as e:
        # Check if an exception was raised and if its type matches the expected exception type.
        if isinstance(expected_output_or_exception, type) and issubclass(expected_output_or_exception, Exception):
            assert isinstance(e, expected_output_or_exception)
        else:
            # If an exception was raised but it was not the expected one, fail the test.
            pytest.fail(f"An unexpected exception was raised: {type(e).__name__}({e})")

