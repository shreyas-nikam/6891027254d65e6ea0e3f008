import pytest
import pandas as pd
import numpy as np

# Keep a placeholder definition_17a36617fe0247b8ad0b7c8e108e3c3b for the import of the module.
# Keep the `your_module` block as it is. DO NOT REPLACE or REMOVE the block.
from definition_17a36617fe0247b8ad0b7c8e108e3c3b import IRRBBEngine

# Helper function to create a base cashflows DataFrame
def create_base_cashflows():
    """
    Creates a sample DataFrame representing instrument cash flows.
    Includes fixed and floating rate instruments with various cashflow types and dates.
    'original_rate' and 'notional' are included for test case calculation transparency,
    as the 'reprice_floating_instruments' method would internally use these or similar concepts.
    """
    return pd.DataFrame({
        'instrument_id': ['FXD001', 'FLT001', 'FXD001', 'FLT001', 'FLT001', 'FLT002', 'FLT002'],
        'cashflow_date': pd.to_datetime(['2023-01-01', '2023-06-01', '2023-07-01', '2023-08-01', '2024-02-01', '2023-03-01', '2023-09-01']),
        'cashflow_type': ['principal', 'interest', 'interest', 'interest', 'principal', 'interest', 'interest'],
        'amount': [10000.0, 20.0, 30.0, 20.0, 10000.0, 10.0, 10.0], # Initial amounts
        'rate_type': ['fixed', 'floating', 'fixed', 'floating', 'floating', 'floating', 'floating'],
        'next_reprice_date': pd.to_datetime([pd.NaT, '2023-07-15', pd.NaT, '2023-07-15', '2023-07-15', '2023-04-01', '2023-04-01']),
        'original_rate': [np.nan, 0.02, 0.03, 0.02, np.nan, 0.01, 0.01], # Rate at which interest was originally calculated
        'notional': [10000, 1000, 1000, 1000, 1000, 500, 500], # Notional for interest calculation (e.g., amount = notional * rate)
        'currency': ['TWD', 'TWD', 'TWD', 'TWD', 'TWD', 'TWD', 'TWD']
    })

# Helper function to create a base scenario yield curve
def create_base_yield_curve():
    """
    Creates a sample scenario yield curve.
    For the purpose of these tests, we assume that `reprice_floating_instruments`
    would derive a new effective rate of 0.04 (4%) for repricing floating instruments
    from this curve based on internal logic (e.g., lookup for a relevant tenor).
    """
    return pd.Series([0.03, 0.035, 0.04], index=['1M', '6M', '1Y'], name='rates')

@pytest.fixture
def irrbb_engine_instance():
    """
    Provides a mock or actual instance of IRRBBEngine for testing.
    Assumes IRRBBEngine can be instantiated with dummy parameters for this method's scope.
    """
    # Create dummy configurations as the IRRBBEngine __init__ requires them
    dummy_positions_df = pd.DataFrame()
    dummy_scenarios_config = {}
    dummy_assumptions_config = {}
    # Instantiate the actual IRRBBEngine from your_module
    return IRRBBEngine(dummy_positions_df, dummy_scenarios_config, dummy_assumptions_config)

@pytest.mark.parametrize("cashflows_df, scenario_yield_curve, expected", [
    # Test Case 1: Nominal Repricing - Floating instrument reprices to a higher rate.
    # FLT001: original_rate 0.02, notional 1000 -> amount 20.0
    # Expected new rate from scenario_yield_curve (e.g., 1Y tenor) = 0.04
    # Expected new amount = 1000 * 0.04 = 40.0
    # FLT002: original_rate 0.01, notional 500 -> amount 10.0
    # Expected new rate from scenario_yield_curve = 0.04
    # Expected new amount = 500 * 0.04 = 20.0
    (
        create_base_cashflows(),
        create_base_yield_curve(),
        pd.DataFrame({
            'instrument_id': ['FXD001', 'FLT001', 'FXD001', 'FLT001', 'FLT001', 'FLT002', 'FLT002'],
            'cashflow_date': pd.to_datetime(['2023-01-01', '2023-06-01', '2023-07-01', '2023-08-01', '2024-02-01', '2023-03-01', '2023-09-01']),
            'cashflow_type': ['principal', 'interest', 'interest', 'interest', 'principal', 'interest', 'interest'],
            'amount': [10000.0, 20.0, 30.0, 40.0, 10000.0, 10.0, 20.0], # Affected: FLT001 (20.0 -> 40.0), FLT002 (10.0 -> 20.0)
            'rate_type': ['fixed', 'floating', 'fixed', 'floating', 'floating', 'floating', 'floating'],
            'next_reprice_date': pd.to_datetime([pd.NaT, '2023-07-15', pd.NaT, '2023-07-15', '2023-07-15', '2023-04-01', '2023-04-01']),
            'original_rate': [np.nan, 0.02, 0.03, 0.02, np.nan, 0.01, 0.01],
            'notional': [10000, 1000, 1000, 1000, 1000, 500, 500],
            'currency': ['TWD', 'TWD', 'TWD', 'TWD', 'TWD', 'TWD', 'TWD']
        })
    ),
    # Test Case 2: No Floating Instruments - DataFrame should remain unchanged.
    (
        pd.DataFrame({
            'instrument_id': ['FXD001', 'FXD002'],
            'cashflow_date': pd.to_datetime(['2023-01-01', '2023-07-01']),
            'cashflow_type': ['principal', 'interest'],
            'amount': [10000.0, 50.0],
            'rate_type': ['fixed', 'fixed'],
            'next_reprice_date': pd.to_datetime([pd.NaT, pd.NaT]),
            'original_rate': [np.nan, 0.05],
            'notional': [10000, 1000],
            'currency': ['TWD', 'TWD']
        }),
        create_base_yield_curve(),
        pd.DataFrame({ # Expected to be identical to input
            'instrument_id': ['FXD001', 'FXD002'],
            'cashflow_date': pd.to_datetime(['2023-01-01', '2023-07-01']),
            'cashflow_type': ['principal', 'interest'],
            'amount': [10000.0, 50.0],
            'rate_type': ['fixed', 'fixed'],
            'next_reprice_date': pd.to_datetime([pd.NaT, pd.NaT]),
            'original_rate': [np.nan, 0.05],
            'notional': [10000, 1000],
            'currency': ['TWD', 'TWD']
        })
    ),
    # Test Case 3: Empty Cashflows DataFrame - Should return an empty DataFrame with same columns.
    (
        pd.DataFrame(columns=[
            'instrument_id', 'cashflow_date', 'cashflow_type', 'amount',
            'rate_type', 'next_reprice_date', 'original_rate', 'notional', 'currency'
        ]),
        create_base_yield_curve(),
        pd.DataFrame(columns=[
            'instrument_id', 'cashflow_date', 'cashflow_type', 'amount',
            'rate_type', 'next_reprice_date', 'original_rate', 'notional', 'currency'
        ])
    ),
    # Test Case 4: Floating instrument with all interest cashflows occurring before its reprice date.
    # No cashflows should be affected.
    (
        pd.DataFrame({
            'instrument_id': ['FLT001'],
            'cashflow_date': pd.to_datetime(['2023-01-01', '2023-03-01']),
            'cashflow_type': ['interest', 'principal'],
            'amount': [20.0, 1000.0],
            'rate_type': ['floating', 'floating'],
            'next_reprice_date': pd.to_datetime(['2023-07-15', '2023-07-15']),
            'original_rate': [0.02, np.nan],
            'notional': [1000, 1000],
            'currency': ['TWD', 'TWD']
        }),
        pd.Series([0.04], index=['1Y'], name='rates'), # New rate 0.04
        pd.DataFrame({ # Expected to be identical to input
            'instrument_id': ['FLT001'],
            'cashflow_date': pd.to_datetime(['2023-01-01', '2023-03-01']),
            'cashflow_type': ['interest', 'principal'],
            'amount': [20.0, 1000.0],
            'rate_type': ['floating', 'floating'],
            'next_reprice_date': pd.to_datetime(['2023-07-15', '2023-07-15']),
            'original_rate': [0.02, np.nan],
            'notional': [1000, 1000],
            'currency': ['TWD', 'TWD']
        })
    ),
    # Test Case 5: Invalid Input Types - `cashflows_df` is not a DataFrame.
    (
        "this_is_a_string", # Invalid type for cashflows_df
        create_base_yield_curve(),
        TypeError # Expected exception
    ),
])
def test_reprice_floating_instruments(irrbb_engine_instance, cashflows_df, scenario_yield_curve, expected):
    """
    Tests the reprice_floating_instruments method for various scenarios including edge cases.
    """
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            irrbb_engine_instance.reprice_floating_instruments(cashflows_df, scenario_yield_curve)
    else:
        result_df = irrbb_engine_instance.reprice_floating_instruments(cashflows_df, scenario_yield_curve)

        # Ensure datetime columns are aligned for comparison, as pd.testing.assert_frame_equal
        # can be strict about datetime types if not handled.
        # Ensure all columns are present and in the same order if strict comparison is desired.
        # For Robustness: Sort by relevant columns before comparison if order might differ.
        sort_cols = ['instrument_id', 'cashflow_date', 'cashflow_type']
        
        pd.testing.assert_frame_equal(
            result_df.sort_values(by=sort_cols).reset_index(drop=True),
            expected.sort_values(by=sort_cols).reset_index(drop=True),
            check_dtype=True,
            check_exact=True # Use check_exact=False with rtol/atol if floating point precision is an issue
                            # For these integer/simple float examples, exact should be fine.
        )