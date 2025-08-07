import pytest
import pandas as pd
from definition_c622e195ad5b41a087a2df9388ae540b import apply_behavioral_assumptions

@pytest.fixture
def base_cashflow_df():
    """
    Provides a base DataFrame with various instruments and behavioral flags for testing.
    """
    data = [
        ('M1', '2024-01-01', 'Principal', 1000.0, 'Mortgage_Prepay'),
        ('M1', '2024-01-01', 'Interest', 50.0, 'Mortgage_Prepay'),
        ('NMD1', '2023-01-01', 'Principal', 5000.0, 'NMD_Savings'),
        ('NMD1', '2023-01-01', 'Interest', 10.0, 'NMD_Savings'),
        ('CL1', '2025-06-30', 'Principal', 2000.0, None),
        ('CL1', '2025-06-30', 'Interest', 100.0, 'Other_Flag'),
    ]
    df = pd.DataFrame(data, columns=['instrument_id', 'cashflow_date', 'cashflow_type', 'cashflow_amount', 'behavioral_flag'])
    df['cashflow_date'] = pd.to_datetime(df['cashflow_date'])
    return df

def test_mortgage_prepayment_flag_application(base_cashflow_df):
    """
    Test that when 'Mortgage_Prepay' is the specified behavioral_flag,
    a 'prepayment_factor' column is added and correctly populated for relevant rows,
    while other behavioral columns are not introduced.
    """
    df = base_cashflow_df.copy()
    prepayment_rate = 0.05
    nmd_beta = 0.5 # These should be ignored by the function if flag is 'Mortgage_Prepay'
    nmd_maturity = 3.0

    result_df = apply_behavioral_assumptions(df, 'Mortgage_Prepay', prepayment_rate, nmd_beta, nmd_maturity)

    # Assert 'prepayment_factor' column is present
    assert 'prepayment_factor' in result_df.columns

    # Assert NMD-specific columns are NOT present, as we only applied 'Mortgage_Prepay' logic
    assert 'applied_nmd_beta' not in result_df.columns
    assert 'applied_nmd_behavioral_maturity_years' not in result_df.columns

    # Check rows with 'Mortgage_Prepay' flag
    mortgage_rows = result_df[result_df['behavioral_flag'] == 'Mortgage_Prepay']
    assert not mortgage_rows.empty
    pd.testing.assert_series_equal(mortgage_rows['prepayment_factor'], pd.Series([(1 - prepayment_rate)] * len(mortgage_rows), index=mortgage_rows.index), check_dtype=False)

    # Check rows without 'Mortgage_Prepay' flag (should have NaN in 'prepayment_factor')
    non_mortgage_rows = result_df[result_df['behavioral_flag'] != 'Mortgage_Prepay']
    assert non_mortgage_rows['prepayment_factor'].isna().all()

def test_nmd_behavioral_flag_application(base_cashflow_df):
    """
    Test that when 'NMD_Savings' is the specified behavioral_flag,
    'applied_nmd_beta' and 'applied_nmd_behavioral_maturity_years' columns are added
    and correctly populated for relevant rows, while other behavioral columns are not introduced.
    """
    df = base_cashflow_df.copy()
    prepayment_rate = 0.05 # This should be ignored by the function if flag is 'NMD_Savings'
    nmd_beta = 0.5
    nmd_maturity = 3.0

    result_df = apply_behavioral_assumptions(df, 'NMD_Savings', prepayment_rate, nmd_beta, nmd_maturity)

    # Assert NMD-specific columns are present
    assert 'applied_nmd_beta' in result_df.columns
    assert 'applied_nmd_behavioral_maturity_years' in result_df.columns

    # Assert 'prepayment_factor' column is NOT present, as we only applied 'NMD_Savings' logic
    assert 'prepayment_factor' not in result_df.columns

    # Check rows with 'NMD_Savings' flag
    nmd_rows = result_df[result_df['behavioral_flag'] == 'NMD_Savings']
    assert not nmd_rows.empty
    pd.testing.assert_series_equal(nmd_rows['applied_nmd_beta'], pd.Series([nmd_beta] * len(nmd_rows), index=nmd_rows.index), check_dtype=False)
    pd.testing.assert_series_equal(nmd_rows['applied_nmd_behavioral_maturity_years'], pd.Series([nmd_maturity] * len(nmd_rows), index=nmd_rows.index), check_dtype=False)

    # Check rows without 'NMD_Savings' flag (should have NaN in NMD-specific columns)
    non_nmd_rows = result_df[result_df['behavioral_flag'] != 'NMD_Savings']
    assert non_nmd_rows['applied_nmd_beta'].isna().all()
    assert non_nmd_rows['applied_nmd_behavioral_maturity_years'].isna().all()

def test_no_behavioral_flag_match_no_dataframe_change(base_cashflow_df):
    """
    Test that if the specified behavioral_flag does not match any known type (e.g., 'Mortgage_Prepay', 'NMD_Savings'),
    the DataFrame is returned completely unchanged (no new columns added, existing data untouched).
    """
    df = base_cashflow_df.copy()
    original_df = df.copy() # Keep a copy for strict comparison
    
    # Use a flag that is not recognized
    result_df = apply_behavioral_assumptions(df, 'Unrecognized_Behavioral_Flag', 0.1, 0.7, 5.0)

    # Assert no new behavioral columns were added
    assert 'prepayment_factor' not in result_df.columns
    assert 'applied_nmd_beta' not in result_df.columns
    assert 'applied_nmd_behavioral_maturity_years' not in result_df.columns
    
    # Assert the entire DataFrame is identical to the original
    pd.testing.assert_frame_equal(original_df, result_df)

def test_empty_dataframe_input_returns_empty_dataframe():
    """
    Test that the function handles an empty input DataFrame gracefully,
    returning an empty DataFrame without errors or adding new columns.
    """
    empty_df = pd.DataFrame(columns=['instrument_id', 'cashflow_date', 'cashflow_type', 'cashflow_amount', 'behavioral_flag'])
    # Ensure 'cashflow_date' is of datetime type for consistency if the function expects it
    empty_df['cashflow_date'] = pd.to_datetime(empty_df['cashflow_date'])

    result_df = apply_behavioral_assumptions(empty_df, 'Mortgage_Prepay', 0.05, 0.5, 3.0)

    # Assert the returned DataFrame is empty and has the same columns as input
    pd.testing.assert_frame_equal(empty_df, result_df)
    # Also assert no new behavioral columns are added since there are no rows to tag
    assert 'prepayment_factor' not in result_df.columns
    assert 'applied_nmd_beta' not in result_df.columns
    assert 'applied_nmd_behavioral_maturity_years' not in result_df.columns

def test_zero_prepayment_rate_sets_factor_to_one(base_cashflow_df):
    """
    Test that when prepayment_rate_annual is 0.0, the 'prepayment_factor' is correctly
    set to 1.0 for 'Mortgage_Prepay' rows, implying no cash flow reduction.
    """
    df = base_cashflow_df.copy()
    prepayment_rate = 0.0 # Zero prepayment
    nmd_beta = 0.5
    nmd_maturity = 3.0

    result_df = apply_behavioral_assumptions(df, 'Mortgage_Prepay', prepayment_rate, nmd_beta, nmd_maturity)

    assert 'prepayment_factor' in result_df.columns
    
    # Check rows with 'Mortgage_Prepay' flag
    mortgage_rows = result_df[result_df['behavioral_flag'] == 'Mortgage_Prepay']
    assert not mortgage_rows.empty
    # Factor should be 1.0 (1 - 0.0)
    pd.testing.assert_series_equal(mortgage_rows['prepayment_factor'], pd.Series([(1 - prepayment_rate)] * len(mortgage_rows), index=mortgage_rows.index), check_dtype=False)
    
    # Check non-Mortgage_Prepay rows still have NaN
    non_mortgage_rows = result_df[result_df['behavioral_flag'] != 'Mortgage_Prepay']
    assert non_mortgage_rows['prepayment_factor'].isna().all()