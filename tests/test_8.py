import pytest
import pandas as pd
from definition_dd5154a830004da6b3593bff37119c22 import generate_basel_shocked_curve

# --- Helper functions to create test data and expected results ---

def create_baseline_curve():
    """Returns a sample baseline DataFrame representing a yield curve."""
    data = {'Tenor': [0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0], # Tenors in years
            'Rate': [0.01, 0.015, 0.02, 0.025, 0.03, 0.035, 0.04]} # Decimal rates
    return pd.DataFrame(data)

def expected_parallel_up_curve(baseline_df, shock_bps):
    """Calculates the expected curve for a Parallel Up scenario."""
    shock_decimal = shock_bps / 10000.0 # Convert basis points to decimal
    expected_df = baseline_df.copy()
    expected_df['Rate'] = expected_df['Rate'] + shock_decimal
    return expected_df

def expected_steepener_curve(baseline_df, shock_short_bps, shock_long_bps):
    """
    Calculates a simplified expected curve for a Steepener scenario.
    This implementation assumes the short shock is applied to the lowest tenor rate
    and the long shock to the highest tenor rate, with linear interpolation
    for intermediate rates. This provides a concrete expected DataFrame for testing
    a stub function where the exact interpolation logic is unknown.
    """
    shock_short_decimal = shock_short_bps / 10000.0
    shock_long_decimal = shock_long_bps / 10000.0

    expected_df = baseline_df.copy()
    
    min_tenor = expected_df['Tenor'].min()
    max_tenor = expected_df['Tenor'].max()

    # Get original rates at min and max tenors
    orig_rate_min_tenor = expected_df.loc[expected_df['Tenor'] == min_tenor, 'Rate'].iloc[0]
    orig_rate_max_tenor = expected_df.loc[expected_df['Tenor'] == max_tenor, 'Rate'].iloc[0]

    # Calculate shocked rates at min and max tenors
    shocked_rate_min_tenor = orig_rate_min_tenor + shock_short_decimal
    shocked_rate_max_tenor = orig_rate_max_tenor + shock_long_decimal

    interpolated_rates = []
    for tenor in expected_df['Tenor']:
        if tenor <= min_tenor: 
            interpolated_rates.append(shocked_rate_min_tenor)
        elif tenor >= max_tenor:
            interpolated_rates.append(shocked_rate_max_tenor)
        else:
            # Linear interpolation between the two shocked endpoints
            rate = shocked_rate_min_tenor + \
                   (shocked_rate_max_tenor - shocked_rate_min_tenor) * \
                   ((tenor - min_tenor) / (max_tenor - min_tenor))
            interpolated_rates.append(rate)
            
    expected_df['Rate'] = interpolated_rates
    return expected_df

# --- Pytest parametrization for test cases ---

@pytest.mark.parametrize(
    "baseline_curve_input, scenario_type, shock_magnitude_bps_short, shock_magnitude_bps_long, expected",
    [
        # Test Case 1: Standard functionality - Parallel Up
        # All rates should shift up by 100 bps (0.01)
        (create_baseline_curve(), 'Parallel Up', 100, 100, expected_parallel_up_curve(create_baseline_curve(), 100)),

        # Test Case 2: Complex scenario - Steepener
        # Short-term rates fall (-50 bps), long-term rates rise (+75 bps).
        # Expected output follows a simplified linear interpolation between shocked endpoints.
        (create_baseline_curve(), 'Steepener', -50, 75, expected_steepener_curve(create_baseline_curve(), -50, 75)),

        # Test Case 3: Edge case - Zero Shock
        # When shock magnitudes are zero, the output curve should be identical to the baseline.
        (create_baseline_curve(), 'Parallel Up', 0, 0, create_baseline_curve()),

        # Test Case 4: Error handling - Invalid Scenario Type
        # Passing an unsupported scenario type should raise a ValueError.
        (create_baseline_curve(), 'NonExistentScenario', 10, 10, ValueError),

        # Test Case 5: Error handling - Non-DataFrame baseline_curve
        # Passing an input for baseline_curve that is not a pandas DataFrame should raise a TypeError.
        ("this is not a pandas DataFrame", 'Parallel Up', 10, 10, TypeError),
    ]
)
def test_generate_basel_shocked_curve(baseline_curve_input, scenario_type, shock_magnitude_bps_short, shock_magnitude_bps_long, expected):
    """
    Tests the generate_basel_shocked_curve function covering various scenarios,
    including expected outputs and error handling for invalid inputs.
    """
    try:
        result = generate_basel_shocked_curve(baseline_curve_input, scenario_type, shock_magnitude_bps_short, shock_magnitude_bps_long)
        
        # If the expected output is a pandas DataFrame, compare them
        # Use pd.testing.assert_frame_equal for robust DataFrame comparison,
        # with atol for floating-point tolerance.
        pd.testing.assert_frame_equal(result, expected, check_dtype=True, check_exact=False, atol=1e-9)

    except Exception as e:
        # If an exception type is expected, assert that the raised exception is of that type.
        assert isinstance(e, expected)