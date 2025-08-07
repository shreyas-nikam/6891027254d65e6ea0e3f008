import pytest
import pandas as pd
from datetime import datetime, timedelta

# Placeholder for the module import
from definition_f16495ee91094d04ae9f61c98a7aa303 import map_cashflows_to_basel_buckets

# Define standard Basel bucket definitions for testing
# These are typical definitions in the format (min_duration, max_duration, unit)
BASEL_BUCKET_DEFS = [
    (0, 1, 'M'),    # 0 to 1 Month
    (1, 3, 'M'),    # 1 to 3 Months
    (3, 6, 'M'),    # 3 to 6 Months
    (6, 12, 'M'),   # 6 to 12 Months
    (1, 2, 'Y'),    # 1 to 2 Years
    (2, 3, 'Y'),    # 2 to 3 Years
    (3, 5, 'Y'),    # 3 to 5 Years
    (5, 10, 'Y'),   # 5 to 10 Years
    (10, float('inf'), 'Y') # >10 Years
]

# Assuming the function generates these specific labels for the 'Basel_Bucket' column
# based on the definitions provided in the notebook specification:
# (0-1M, 1-3M, 3-6M, 6-12M, 1-2Y, 2-3Y, 3-5Y, 5-10Y, >10Y)

def test_standard_cashflows_mapping():
    """
    Tests the function with a mix of payment dates covering various standard Basel buckets.
    Ensures correct assignment of 'Basel_Bucket' for typical scenarios.
    """
    valuation_date = datetime(2023, 1, 1)
    cashflow_df = pd.DataFrame({
        'cashflow_id': [1, 2, 3, 4, 5, 6, 7, 8],
        'payment_date': [
            datetime(2023, 1, 15),  # ~0.5 months -> 0-1M
            datetime(2023, 2, 15),  # ~1.5 months -> 1-3M
            datetime(2023, 5, 1),   # ~4 months -> 3-6M
            datetime(2023, 10, 1),  # ~9 months -> 6-12M
            datetime(2024, 6, 1),   # ~1.5 years -> 1-2Y
            datetime(2025, 6, 1),   # ~2.5 years -> 2-3Y
            datetime(2027, 6, 1),   # ~4.5 years -> 3-5Y
            datetime(2030, 6, 1),   # ~7.5 years -> 5-10Y
        ],
        'amount': [100, 200, 300, 400, 500, 600, 700, 800]
    })

    result_df = map_cashflows_to_basel_buckets(cashflow_df.copy(), valuation_date, BASEL_BUCKET_DEFS)

    expected_buckets = [
        '0-1M', '1-3M', '3-6M', '6-12M', '1-2Y', '2-3Y', '3-5Y', '5-10Y'
    ]
    pd.testing.assert_series_equal(result_df['Basel_Bucket'], pd.Series(expected_buckets, name='Basel_Bucket'), check_dtype=False)
    assert 'Basel_Bucket' in result_df.columns
    assert len(result_df) == len(cashflow_df)

def test_empty_dataframe_input():
    """
    Tests the function's behavior with an empty cash flow DataFrame.
    It should return an empty DataFrame with the 'Basel_Bucket' column added.
    """
    valuation_date = datetime(2023, 1, 1)
    cashflow_df = pd.DataFrame(columns=['cashflow_id', 'payment_date', 'amount'])

    result_df = map_cashflows_to_basel_buckets(cashflow_df.copy(), valuation_date, BASEL_BUCKET_DEFS)

    assert isinstance(result_df, pd.DataFrame)
    assert 'Basel_Bucket' in result_df.columns
    assert result_df.empty
    assert result_df.shape[1] == len(cashflow_df.columns) + 1 # Original columns + new 'Basel_Bucket'

def test_boundary_cashflows_mapping():
    """
    Tests cash flows positioned exactly on or very near bucket boundaries,
    including cash flows on the valuation date itself.
    Assumes buckets are defined such that 0-1M includes up to 1 month duration.
    """
    valuation_date = datetime(2023, 1, 1)
    cashflow_df = pd.DataFrame({
        'cashflow_id': [9, 10, 11, 12, 13],
        'payment_date': [
            valuation_date,                           # Duration = 0 -> 0-1M
            valuation_date + timedelta(days=29),      # ~0.96 months -> 0-1M
            valuation_date + timedelta(days=30),      # ~1 month. Assuming 1 month duration is included in 0-1M bucket
            valuation_date + timedelta(days=31),      # ~1.03 months -> 1-3M
            datetime(2033, 1, 1) + timedelta(days=1)  # Exactly 10 years and 1 day -> >10Y
        ],
        'amount': [10, 20, 30, 40, 50]
    })

    result_df = map_cashflows_to_basel_buckets(cashflow_df.copy(), valuation_date, BASEL_BUCKET_DEFS)

    expected_buckets = [
        '0-1M', # Valuation date
        '0-1M', # <1 month
        '0-1M', # ~1 month (inclusive of 1 month duration)
        '1-3M', # >1 month
        '>10Y'  # >10 years
    ]
    pd.testing.assert_series_equal(result_df['Basel_Bucket'], pd.Series(expected_buckets, name='Basel_Bucket'), check_dtype=False)

def test_cashflows_beyond_last_bucket():
    """
    Tests that cash flows with payment dates far in the future are correctly categorized
    into the last (e.g., '>10Y') bucket.
    """
    valuation_date = datetime(2023, 1, 1)
    cashflow_df = pd.DataFrame({
        'cashflow_id': [14, 15, 16],
        'payment_date': [
            datetime(2033, 1, 2), # Clearly >10Y (10 years and 1 day)
            datetime(2035, 6, 1), # 12.5 years
            datetime(2040, 1, 1)  # 17 years
        ],
        'amount': [1000, 2000, 3000]
    })

    result_df = map_cashflows_to_basel_buckets(cashflow_df.copy(), valuation_date, BASEL_BUCKET_DEFS)

    expected_buckets = [
        '>10Y',
        '>10Y',
        '>10Y'
    ]
    pd.testing.assert_series_equal(result_df['Basel_Bucket'], pd.Series(expected_buckets, name='Basel_Bucket'), check_dtype=False)

def test_missing_payment_date_column():
    """
    Tests error handling when the 'cashflow_df' is missing the required 'payment_date' column.
    Should raise a KeyError.
    """
    valuation_date = datetime(2023, 1, 1)
    # DataFrame without 'payment_date' column
    cashflow_df = pd.DataFrame({
        'cashflow_id': [1, 2],
        'some_other_date_col': [datetime(2023, 2, 1), datetime(2024, 1, 1)],
        'amount': [100, 200]
    })

    with pytest.raises(KeyError, match="payment_date"):
        map_cashflows_to_basel_buckets(cashflow_df, valuation_date, BASEL_BUCKET_DEFS)