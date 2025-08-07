import pytest
import pandas as pd
from definition_42b7e5a83c494470850b400ab2d4df33 import report_delta_eve_as_percentage_of_tier1

@pytest.mark.parametrize(
    "delta_eve_results, tier1_capital, expected",
    [
        # Test 1: Comprehensive Scenarios (Standard, Zero, Negative, Large Delta EVEs)
        # Covers expected functionality, including positive, negative, and zero delta EVE values,
        # and varying magnitudes.
        (
            {
                "Parallel Up": 1000.0,
                "Parallel Down": -500.0,
                "Steepener": 200.0,
                "Flattener": 0.0,
                "Short Up": 50000.0,
                "Short Down": -10.0,
            },
            10000.0,
            pd.DataFrame([
                {"Scenario": "Parallel Up", "Delta EVE (% Tier 1 Capital)": 10.0},
                {"Scenario": "Parallel Down", "Delta EVE (% Tier 1 Capital)": -5.0},
                {"Scenario": "Steepener", "Delta EVE (% Tier 1 Capital)": 2.0},
                {"Scenario": "Flattener", "Delta EVE (% Tier 1 Capital)": 0.0},
                {"Scenario": "Short Up", "Delta EVE (% Tier 1 Capital)": 500.0},
                {"Scenario": "Short Down", "Delta EVE (% Tier 1 Capital)": -0.1},
            ]),
        ),
        # Test 2: Edge Case - Zero Tier 1 Capital
        # This should typically result in an error (e.g., ValueError or ZeroDivisionError)
        # as division by zero is undefined and represents an invalid financial state.
        (
            {"Parallel Up": 1000.0},
            0.0,
            ValueError, # Assuming a ValueError is raised for this business rule violation
        ),
        # Test 3: Edge Case - Empty delta_eve_results dictionary
        # If no scenarios are provided, the function should return an empty DataFrame with the correct columns.
        (
            {},
            10000.0,
            pd.DataFrame(columns=["Scenario", "Delta EVE (% Tier 1 Capital)"]),
        ),
        # Test 4: Edge Case - Invalid type for delta_eve_results
        # Input for delta_eve_results is not a dictionary. Expecting a TypeError.
        (
            [100.0, 200.0], # Invalid type: list instead of dict
            10000.0,
            TypeError,
        ),
        # Test 5: Edge Case - Invalid type for tier1_capital
        # Input for tier1_capital is not a float. Expecting a TypeError.
        (
            {"Parallel Up": 1000.0},
            "invalid_capital", # Invalid type: string instead of float
            TypeError,
        ),
    ]
)
def test_report_delta_eve_as_percentage_of_tier1(delta_eve_results, tier1_capital, expected):
    try:
        result_df = report_delta_eve_as_percentage_of_tier1(delta_eve_results, tier1_capital)
        
        # If we reach here, no exception was raised.
        # Ensure that 'expected' is not an exception type, but a pandas DataFrame.
        assert not isinstance(expected, type), f"Expected exception type {expected} but got a DataFrame result."

        # Sort both DataFrames by the 'Scenario' column to ensure consistent comparison
        # regardless of dictionary iteration order in the function's implementation.
        result_df_sorted = result_df.sort_values(by="Scenario").reset_index(drop=True)
        expected_output_sorted = expected.sort_values(by="Scenario").reset_index(drop=True)

        pd.testing.assert_frame_equal(
            result_df_sorted,
            expected_output_sorted,
            check_dtype=False, # Allow for minor differences in pandas' dtype inference (e.g., float64 vs float32)
            check_less_precise=True # Allow for floating point precision differences
        )
    except Exception as e:
        # If an exception was raised, ensure that 'expected' is indeed an exception type
        # and that the raised exception matches the expected type.
        assert isinstance(expected, type), f"Expected DataFrame but an exception {type(e).__name__} was raised."
        assert isinstance(e, expected), f"Expected {expected.__name__} but got {type(e).__name__}"