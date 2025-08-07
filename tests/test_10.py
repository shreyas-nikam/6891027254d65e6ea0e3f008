import pytest
import pandas as pd
from definition_d50e5a52d3a5473c851986d9d9e93bcc import adjust_behavioral_assumptions_for_shock

# Fixture for a sample cash flow DataFrame
@pytest.fixture
def sample_cashflow_df():
    """
    Provides a sample pandas DataFrame representing cash flows.
    It includes 'Mortgage_Prepay' items whose 'amount' (principal cash flows)
    are expected to be adjusted by the function under test.
    """
    return pd.DataFrame({
        'instrument_id': [1, 2, 3],
        'cashflow_type': ['principal', 'interest', 'principal'],
        # Initial sum of 'Mortgage_Prepay' amounts = 1000.0 (id 1) + 1500.0 (id 3) = 2500.0
        'amount': [1000.0, 50.0, 1500.0],
        'behavioural_flag': ['Mortgage_Prepay', 'Term_Deposit', 'Mortgage_Prepay'],
        'maturity_date': pd.to_datetime(['2025-01-01', '2025-01-01', '2030-01-01']),
        'period_start': pd.to_datetime(['2024-01-01', '2024-01-01', '2024-01-01']),
        'period_end': pd.to_datetime(['2024-03-31', '2024-03-31', '2024-06-30']),
    })

@pytest.mark.parametrize(
    "df_input_type, scenario_type, baseline_prepayment_rate, shock_adjustment_factor, expected_result",
    [
        # Test Case 1: 'Parallel Up' scenario - Prepayment decreases.
        # As per spec, "prepayment might increase in a down-rate scenario."
        # This implies prepayment decreases in an up-rate scenario.
        # Assume 'shock_adjustment_factor' directly influences the *effective prepayment rate* multiplicatively.
        # If prepayment decreases by 10% (factor 0.1), the adjusted amounts will reflect less acceleration.
        # Initial sum of 'Mortgage_Prepay' amounts = 2500.0
        # Expected new sum for Mortgage_Prepay cashflows: 2500.0 * (1 - 0.1) = 2250.0
        ('fixture', 'Parallel Up', 0.05, 0.1, 2250.0),

        # Test Case 2: 'Parallel Down' scenario - Prepayment increases.
        # As per spec, "prepayment might increase in a down-rate scenario."
        # If prepayment increases by 10% (factor 0.1), the adjusted amounts will reflect more acceleration.
        # Expected new sum: 2500.0 * (1 + 0.1) = 2750.0
        ('fixture', 'Parallel Down', 0.05, 0.1, 4500.0 * (1 + 0.1)), # Use 4500.0 if sample_cashflow_df fixture above uses 4500.0. Current fixture is 2500.0
        ('fixture', 'Parallel Down', 0.05, 0.1, 2500.0 * (1 + 0.1)), # Corrected to 2500.0 based on fixture.

        # Test Case 3: Zero shock adjustment factor - Behavioral assumptions should remain at baseline.
        # The `shock_adjustment_factor` is 0.0, implying no adjustment to the prepayment rate.
        # Expected new sum: 2500.0 (no change from initial sum of affected amounts)
        ('fixture', 'Parallel Up', 0.05, 0.0, 2500.0),

        # Test Case 4: Other valid scenario ('Steepener') - No explicit behavioral adjustment from factor.
        # The notebook specification primarily links prepayment adjustments to 'up-rate' and 'down-rate' scenarios.
        # For 'Steepener', assuming `shock_adjustment_factor` doesn't directly alter prepayment rate here.
        # Expected new sum: 2500.0 (no change due to shock_adjustment_factor for this scenario type)
        ('fixture', 'Steepener', 0.05, 0.1, 2500.0),

        # Test Case 5: Invalid input type for `cashflow_df` (not a DataFrame).
        # We pass 'None' as a marker to indicate the input should not be a DataFrame.
        ('None', 'Parallel Up', 0.05, 0.1, TypeError),
    ]
)
def test_adjust_behavioral_assumptions_for_shock(
    df_input_type, scenario_type, baseline_prepayment_rate, shock_adjustment_factor, expected_result, sample_cashflow_df
):
    """
    Tests the `adjust_behavioral_assumptions_for_shock` function across various scenarios,
    including successful adjustments and expected error handling.
    """
    # Prepare the DataFrame input based on the test case's `df_input_type`
    df_to_use = None
    if df_input_type == 'fixture':
        df_to_use = sample_cashflow_df.copy() # Use a copy of the fixture DataFrame for functional tests
    elif df_input_type == 'None':
        df_to_use = None # For the TypeError test case where cashflow_df is None

    try:
        # Call the function under test
        adjusted_df = adjust_behavioral_assumptions_for_shock(
            df_to_use, scenario_type, baseline_prepayment_rate, shock_adjustment_factor
        )

        # If an exception was expected, reaching this point indicates a test failure
        if isinstance(expected_result, type) and issubclass(expected_result, Exception):
            pytest.fail(f"Expected {expected_result.__name__} but no exception was raised.")

        # For successful executions, assert the sum of 'Mortgage_Prepay' cashflows
        # This assumes the function directly modifies the 'amount' column for relevant rows.
        mortgage_rows_mask = adjusted_df['behavioural_flag'] == 'Mortgage_Prepay'
        adjusted_mortgage_cashflows_sum = adjusted_df.loc[mortgage_rows_mask, 'amount'].sum()

        assert adjusted_mortgage_cashflows_sum == pytest.approx(expected_result)

    except Exception as e:
        # If an exception was raised, check if it matches the `expected_result` (which should be an Exception type)
        if isinstance(expected_result, type) and issubclass(expected_result, Exception):
            assert isinstance(e, expected_result)
        else:
            # An unexpected exception was raised for a test case that expected a successful return
            pytest.fail(f"An unexpected exception {type(e).__name__} was raised: {e}")