import pytest
import pandas as pd
from datetime import datetime

# Keep this placeholder
from definition_0009a37ef65e411ebbe6c267fce43739 import reprice_floating_instrument_cashflows_under_shock

# Helper to create a base cashflow df template with specified dtypes for consistency
def create_cashflow_df_template():
    return pd.DataFrame(columns=[
        'date', 
        'cash_flow_type', 
        'amount', 
        'is_floating_rate', 
        'original_principal' # Assumed required for re-calculating interest
    ]).astype({
        'date': 'datetime64[ns]', 
        'cash_flow_type': 'object', 
        'amount': 'float64', 
        'is_floating_rate': 'bool',
        'original_principal': 'float64'
    })

# Test 1: Basic Floating Repricing - Some cash flows re-priced, some remain unchanged
def test_reprice_floating_instrument_cashflows_basic():
    next_repricing_date = pd.Timestamp('2023-07-01')
    
    # instrument_cashflow_df:
    # CF1: Floating, before repricing date -> amount remains unchanged
    # CF2: Floating, after repricing date, interest -> amount re-priced
    # CF3: Floating, after repricing date, interest -> amount re-priced
    # CF4: Floating, after repricing date, principal -> amount remains unchanged (principals are not re-priced by interest shocks)
    instrument_cashflow_data = [
        {'date': pd.Timestamp('2023-04-01'), 'cash_flow_type': 'interest', 'amount': 100.0, 'is_floating_rate': True, 'original_principal': 10000.0},
        {'date': pd.Timestamp('2023-10-01'), 'cash_flow_type': 'interest', 'amount': 100.0, 'is_floating_rate': True, 'original_principal': 10000.0},
        {'date': pd.Timestamp('2024-04-01'), 'cash_flow_type': 'interest', 'amount': 100.0, 'is_floating_rate': True, 'original_principal': 10000.0},
        {'date': pd.Timestamp('2024-10-01'), 'cash_flow_type': 'principal', 'amount': 1000.0, 'is_floating_rate': True, 'original_principal': 9000.0}, 
    ]
    instrument_cashflow_df = pd.DataFrame(instrument_cashflow_data, dtype=object).astype({
        'date': 'datetime64[ns]', 'cash_flow_type': 'object', 'amount': 'float64', 
        'is_floating_rate': 'bool', 'original_principal': 'float64'
    })

    # instrument_data: Includes 'next_repricing_date', 'index' (e.g., 'EIBOR'), 'spread_bps'
    instrument_data = pd.Series({
        'next_repricing_date': next_repricing_date,
        'index': 'EIBOR', # Name of the index, not a rate
        'spread_bps': 50 # 0.50%
    }).astype({
        'next_repricing_date': 'datetime64[ns]',
        'index': 'object',
        'spread_bps': 'int64'
    })

    # shocked_curve: Contains date-rate pairs to be used for repricing
    shocked_curve = pd.DataFrame([
        {'date': pd.Timestamp('2023-10-01'), 'rate': 0.03},
        {'date': pd.Timestamp('2024-04-01'), 'rate': 0.035},
        {'date': pd.Timestamp('2024-10-01'), 'rate': 0.04}, 
    ]).astype({'date': 'datetime64[ns]', 'rate': 'float64'})
    
    # Expected re-priced amounts calculation logic:
    # New Interest Amount = original_principal * (shocked_rate + (spread_bps / 10000))
    # CF1 amount: 100.0 (unchanged, as its date < next_repricing_date)
    # CF2 amount: 10000.0 * (0.03 + 0.005) = 350.0
    # CF3 amount: 10000.0 * (0.035 + 0.005) = 400.0
    # CF4 amount: 1000.0 (principal, unchanged)

    expected_data = [
        {'date': pd.Timestamp('2023-04-01'), 'cash_flow_type': 'interest', 'amount': 100.0, 'is_floating_rate': True, 'original_principal': 10000.0},
        {'date': pd.Timestamp('2023-10-01'), 'cash_flow_type': 'interest', 'amount': 350.0, 'is_floating_rate': True, 'original_principal': 10000.0},
        {'date': pd.Timestamp('2024-04-01'), 'cash_flow_type': 'interest', 'amount': 400.0, 'is_floating_rate': True, 'original_principal': 10000.0},
        {'date': pd.Timestamp('2024-10-01'), 'cash_flow_type': 'principal', 'amount': 1000.0, 'is_floating_rate': True, 'original_principal': 9000.0},
    ]
    expected_df = pd.DataFrame(expected_data, dtype=object).astype({
        'date': 'datetime64[ns]', 'cash_flow_type': 'object', 'amount': 'float64', 
        'is_floating_rate': 'bool', 'original_principal': 'float64'
    })

    result_df = reprice_floating_instrument_cashflows_under_shock(
        instrument_cashflow_df.copy(), instrument_data.copy(), shocked_curve.copy()
    )

    pd.testing.assert_frame_equal(result_df, expected_df, check_dtype=True, check_exact=False, atol=1e-9)

# Test 2: Fixed Rate Instrument - No Repricing Expected
def test_reprice_fixed_instrument_no_change():
    instrument_cashflow_data = [
        {'date': pd.Timestamp('2023-04-01'), 'cash_flow_type': 'interest', 'amount': 100.0, 'is_floating_rate': False, 'original_principal': 10000.0},
        {'date': pd.Timestamp('2023-10-01'), 'cash_flow_type': 'principal', 'amount': 1000.0, 'is_floating_rate': False, 'original_principal': 10000.0},
    ]
    instrument_cashflow_df = pd.DataFrame(instrument_cashflow_data, dtype=object).astype({
        'date': 'datetime64[ns]', 'cash_flow_type': 'object', 'amount': 'float64', 
        'is_floating_rate': 'bool', 'original_principal': 'float64'
    })
    instrument_data = pd.Series({
        'next_repricing_date': pd.Timestamp('2023-07-01'),
        'index': 'FIXED_RATE',
        'spread_bps': 0
    }).astype({
        'next_repricing_date': 'datetime64[ns]',
        'index': 'object',
        'spread_bps': 'int64'
    })
    shocked_curve = pd.DataFrame([
        {'date': pd.Timestamp('2023-04-01'), 'rate': 0.02},
        {'date': pd.Timestamp('2023-10-01'), 'rate': 0.03},
    ]).astype({'date': 'datetime64[ns]', 'rate': 'float64'})

    expected_df = instrument_cashflow_df.copy() # Expect no changes for fixed-rate instruments

    result_df = reprice_floating_instrument_cashflows_under_shock(
        instrument_cashflow_df.copy(), instrument_data.copy(), shocked_curve.copy()
    )
    
    pd.testing.assert_frame_equal(result_df, expected_df, check_dtype=True)

# Test 3: Floating Instrument, all cash flows occur before the next repricing date -> No Repricing
def test_reprice_floating_instrument_before_repricing_date():
    instrument_cashflow_data = [
        {'date': pd.Timestamp('2023-04-01'), 'cash_flow_type': 'interest', 'amount': 100.0, 'is_floating_rate': True, 'original_principal': 10000.0},
        {'date': pd.Timestamp('2023-05-01'), 'cash_flow_type': 'interest', 'amount': 100.0, 'is_floating_rate': True, 'original_principal': 10000.0},
    ]
    instrument_cashflow_df = pd.DataFrame(instrument_cashflow_data, dtype=object).astype({
        'date': 'datetime64[ns]', 'cash_flow_type': 'object', 'amount': 'float64', 
        'is_floating_rate': 'bool', 'original_principal': 'float64'
    })
    instrument_data = pd.Series({
        'next_repricing_date': pd.Timestamp('2023-07-01'), # All CFs are before this date
        'index': 'EIBOR',
        'spread_bps': 50
    }).astype({
        'next_repricing_date': 'datetime64[ns]',
        'index': 'object',
        'spread_bps': 'int64'
    })
    shocked_curve = pd.DataFrame([
        {'date': pd.Timestamp('2023-04-01'), 'rate': 0.02},
        {'date': pd.Timestamp('2023-05-01'), 'rate': 0.025},
    ]).astype({'date': 'datetime64[ns]', 'rate': 'float64'})

    expected_df = instrument_cashflow_df.copy() # Expect no changes

    result_df = reprice_floating_instrument_cashflows_under_shock(
        instrument_cashflow_df.copy(), instrument_data.copy(), shocked_curve.copy()
    )

    pd.testing.assert_frame_equal(result_df, expected_df, check_dtype=True)

# Test 4: Empty Cashflow DataFrame Input - Should return an empty DataFrame with correct columns/dtypes
def test_reprice_empty_cashflow_df():
    instrument_cashflow_df = create_cashflow_df_template() 
    instrument_data = pd.Series({
        'next_repricing_date': pd.Timestamp('2023-07-01'),
        'index': 'EIBOR',
        'spread_bps': 50
    }).astype({
        'next_repricing_date': 'datetime64[ns]',
        'index': 'object',
        'spread_bps': 'int64'
    })
    shocked_curve = pd.DataFrame([
        {'date': pd.Timestamp('2023-10-01'), 'rate': 0.03},
    ]).astype({'date': 'datetime64[ns]', 'rate': 'float64'})

    result_df = reprice_floating_instrument_cashflows_under_shock(
        instrument_cashflow_df.copy(), instrument_data.copy(), shocked_curve.copy()
    )

    pd.testing.assert_frame_equal(result_df, instrument_cashflow_df, check_dtype=True) 

# Test 5: Invalid Input - Missing essential columns in any of the input DataFrames/Series
@pytest.mark.parametrize("cashflow_df_setup, instrument_data_setup, shocked_curve_setup, error_type", [
    # Missing 'date' in instrument_cashflow_df
    (pd.DataFrame([{'cash_flow_type': 'interest', 'amount': 100.0, 'is_floating_rate': True, 'original_principal': 10000.0}]), None, None, KeyError),
    # Missing 'is_floating_rate' in instrument_cashflow_df
    (pd.DataFrame([{'date': pd.Timestamp('2023-04-01'), 'cash_flow_type': 'interest', 'amount': 100.0, 'original_principal': 10000.0}]), None, None, KeyError),
    # Missing 'next_repricing_date' in instrument_data
    (None, pd.Series({'index': 'EIBOR', 'spread_bps': 50}), None, KeyError),
    # Missing 'rate' in shocked_curve
    (None, None, pd.DataFrame([{'date': pd.Timestamp('2023-10-01')}]).astype({'date': 'datetime64[ns]'}), KeyError), 
    # Missing 'date' in shocked_curve
    (None, None, pd.DataFrame([{'rate': 0.03}]).astype({'rate': 'float64'}), KeyError), 
])
def test_reprice_floating_instrument_cashflows_invalid_input(cashflow_df_setup, instrument_data_setup, shocked_curve_setup, error_type):
    # Base valid inputs to substitute or use when others are specifically tested for invalidity
    base_cashflow_df = pd.DataFrame([
        {'date': pd.Timestamp('2023-04-01'), 'cash_flow_type': 'interest', 'amount': 100.0, 'is_floating_rate': True, 'original_principal': 10000.0}
    ], dtype=object).astype({
        'date': 'datetime64[ns]', 'cash_flow_type': 'object', 'amount': 'float64', 
        'is_floating_rate': 'bool', 'original_principal': 'float64'
    })
    base_instrument_data = pd.Series({
        'next_repricing_date': pd.Timestamp('2023-07-01'),
        'index': 'EIBOR',
        'spread_bps': 50
    }).astype({
        'next_repricing_date': 'datetime64[ns]',
        'index': 'object',
        'spread_bps': 'int64'
    })
    base_shocked_curve = pd.DataFrame([
        {'date': pd.Timestamp('2023-10-01'), 'rate': 0.03}
    ]).astype({'date': 'datetime64[ns]', 'rate': 'float64'})
    
    # Assign inputs based on test parameters
    cashflow_df_input = cashflow_df_setup if cashflow_df_setup is not None else base_cashflow_df
    instrument_data_input = instrument_data_setup if instrument_data_setup is not None else base_instrument_data
    shocked_curve_input = shocked_curve_setup if shocked_curve_setup is not None else base_shocked_curve

    with pytest.raises(error_type):
        reprice_floating_instrument_cashflows_under_shock(
            cashflow_df_input, instrument_data_input, shocked_curve_input
        )