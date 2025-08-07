import pytest
import pandas as pd
from datetime import date, timedelta

# Placeholder for the module import
from definition_c6e7c52e192c4025b2b9c6c751170c35 import calculate_cashflows_for_instrument

@pytest.mark.parametrize("instrument_data, baseline_curve, expected_result", [
    # Test Case 1: Standard fixed-rate instrument - checks for DataFrame structure and expected columns.
    (
        pd.Series({
            'instrument_id': 'fixed_loan_001',
            'category': 'asset',
            'balance': 100000.0,
            'rate_type': 'fixed',
            'current_rate': 0.05,
            'payment_freq': 'Annual',
            'maturity_date': date(2025, 12, 31),
            'next_repricing_date': date(2025, 12, 31) # For fixed, typically matches maturity or current date
        }),
        pd.DataFrame({'Date': [date(2023, 1, 1), date(2025, 12, 31)], 'Rate': [0.03, 0.04]}),
        'dataframe_check' # Sentinel to indicate expected DataFrame properties
    ),
    # Test Case 2: Standard floating-rate instrument - checks for DataFrame structure and expected columns.
    (
        pd.Series({
            'instrument_id': 'float_loan_002',
            'category': 'asset',
            'balance': 50000.0,
            'rate_type': 'floating',
            'index': 'EIBOR',
            'spread_bps': 150, # 1.5%
            'current_rate': 0.035, # Example initial rate
            'payment_freq': 'Quarterly',
            'maturity_date': date(2026, 6, 30),
            'next_repricing_date': date(2024, 3, 31) # Next repricing point
        }),
        pd.DataFrame({'Date': [date(2023, 1, 1), date(2026, 6, 30)], 'Rate': [0.03, 0.05]}),
        'dataframe_check'
    ),
    # Test Case 3: Instrument with zero balance - expects an empty DataFrame.
    (
        pd.Series({
            'instrument_id': 'zero_bal_003',
            'category': 'liability',
            'balance': 0.0, # Zero balance
            'rate_type': 'fixed',
            'current_rate': 0.01,
            'payment_freq': 'Monthly',
            'maturity_date': date(2024, 1, 1),
            'next_repricing_date': date(2024, 1, 1)
        }),
        pd.DataFrame({'Date': [date(2023, 1, 1)], 'Rate': [0.01]}),
        pd.DataFrame() # Expect an empty DataFrame
    ),
    # Test Case 4: Invalid instrument_data type (e.g., dict instead of pandas.Series) - expects TypeError.
    (
        {'instrument_id': 'invalid_type_004', 'balance': 1000}, # Incorrect type
        pd.DataFrame({'Date': [date(2023, 1, 1)], 'Rate': [0.01]}),
        TypeError
    ),
    # Test Case 5: Missing essential column in instrument_data - expects KeyError or ValueError.
    (
        pd.Series({
            'instrument_id': 'missing_col_005',
            'category': 'asset',
            'balance': 10000.0,
            'rate_type': 'fixed',
            # 'payment_freq' is deliberately missing here
            'maturity_date': date(2025, 12, 31),
            'next_repricing_date': date(2025, 12, 31)
        }),
        pd.DataFrame({'Date': [date(2023, 1, 1)], 'Rate': [0.01]}),
        (KeyError, ValueError) # Expected to raise either KeyError (if accessing directly) or ValueError (if validated)
    ),
])
def test_calculate_cashflows_for_instrument(instrument_data, baseline_curve, expected_result):
    try:
        result = calculate_cashflows_for_instrument(instrument_data, baseline_curve)
        
        # Handle cases expecting a DataFrame output
        if expected_result == 'dataframe_check':
            assert isinstance(result, pd.DataFrame)
            expected_columns = ['Date', 'Type', 'Amount', 'Instrument_ID', 'Category']
            assert all(col in result.columns for col in expected_columns)
            assert not result.empty, "DataFrame should not be empty for a non-zero balance instrument."
            # Further assertions on content (e.g., number of rows, specific values)
            # would require knowledge of the exact cash flow calculation logic,
            # which is not available in a 'pass' stub.
            assert result['Instrument_ID'].iloc[0] == instrument_data['instrument_id']
            assert result['Category'].iloc[0] == instrument_data['category']

        elif isinstance(expected_result, pd.DataFrame) and expected_result.empty:
            assert isinstance(result, pd.DataFrame)
            assert result.empty, "Expected an empty DataFrame for zero balance instrument."
            expected_columns = ['Date', 'Type', 'Amount', 'Instrument_ID', 'Category']
            assert all(col in result.columns for col in expected_columns) # Ensure columns exist even if empty
            
    except Exception as e:
        # Handle cases expecting an exception
        if isinstance(expected_result, tuple): # For multiple possible exceptions
            assert isinstance(e, expected_result)
        else:
            assert isinstance(e, expected_result)