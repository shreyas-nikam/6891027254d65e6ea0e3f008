import pytest
import pandas as pd
import os
from datetime import datetime

# Keep the your_module block as it is. DO NOT REPLACE or REMOVE the block.
# definition_ff760c98be3a486e98510eb0aa9da3bb
from definition_ff760c98be3a486e98510eb0aa9da3bb import preprocess_positions_data

# Define a temporary directory for test outputs to ensure clean test runs
@pytest.fixture(scope="module")
def temp_dir():
    test_dir = "test_output_temp_dir"
    os.makedirs(test_dir, exist_ok=True)
    yield test_dir
    # Clean up after all tests in the module are done
    for f in os.listdir(test_dir):
        os.remove(os.path.join(test_dir, f))
    os.rmdir(test_dir)

def test_preprocess_positions_data_happy_path(temp_dir):
    """
    Test the basic functionality with a typical input:
    - Date columns conversion
    - Missing float spreads handling (filling with 0)
    - NMD tagging ('core' vs 'non-core')
    - Saving to PKL file
    """
    input_data = {
        'instrument_id': [1, 2, 3, 4, 5],
        'instrument_type': ['Loan', 'NMD', 'Bond', 'NMD', 'Deposit'],
        'maturity_date': ['2023-01-15', 'N/A', '2025-12-31', '2024-06-01', '2023-03-01'],
        'next_reprice_date': ['2022-07-01', 'N/A', '2023-01-01', 'N/A', '2023-03-01'],
        'spread_bps': [10.5, None, 5.0, '', 15.0], # Test float, None, and empty string
        'core_fraction': [0.0, 0.8, 0.0, 0.0, 0.0], # Test core_fraction for NMD tagging
        'notional_amt': [1000, 500, 2000, 750, 1200]
    }
    input_df = pd.DataFrame(input_data)
    output_file = os.path.join(temp_dir, 'happy_path_clean_positions.pkl')

    preprocess_positions_data(input_df, output_file)

    assert os.path.exists(output_file)
    cleaned_df = pd.read_pickle(output_file)

    # Assert date columns are datetime objects and handled NaT correctly
    assert pd.api.types.is_datetime64_any_dtype(cleaned_df['maturity_date'])
    assert pd.api.types.is_datetime64_any_dtype(cleaned_df['next_reprice_date'])
    # N/A values in 'maturity_date' and 'next_reprice_date' for NMDs should be NaT
    assert pd.isna(cleaned_df.loc[cleaned_df['instrument_type'] == 'NMD', 'maturity_date']).all()
    assert pd.isna(cleaned_df.loc[cleaned_df['instrument_type'] == 'NMD', 'next_reprice_date']).all()
    assert cleaned_df.loc[0, 'maturity_date'] == datetime(2023, 1, 15)

    # Assert spread_bps are numeric and NaNs/empty strings are filled with 0
    assert pd.api.types.is_numeric_dtype(cleaned_df['spread_bps'])
    assert cleaned_df.loc[1, 'spread_bps'] == 0.0 # None
    assert cleaned_df.loc[3, 'spread_bps'] == 0.0 # ''

    # Assert NMDs are tagged 'core' vs 'non-core'
    # Assuming the function adds a column named 'nmd_classification'
    assert 'nmd_classification' in cleaned_df.columns
    assert cleaned_df.loc[1, 'nmd_classification'] == 'core' # NMD with core_fraction > 0.5 (assuming threshold)
    assert cleaned_df.loc[3, 'nmd_classification'] == 'non-core' # NMD with core_fraction == 0
    assert cleaned_df.loc[0, 'nmd_classification'] == 'N/A' # Not an NMD

def test_preprocess_positions_data_empty_dataframe(temp_dir):
    """
    Test handling of an empty input DataFrame.
    The function should run without error and save an empty PKL file
    with the expected schema (columns).
    """
    input_df = pd.DataFrame(columns=[
        'instrument_id', 'instrument_type', 'maturity_date',
        'next_reprice_date', 'spread_bps', 'core_fraction'
    ])
    output_file = os.path.join(temp_dir, 'empty_df_clean_positions.pkl')

    preprocess_positions_data(input_df, output_file)

    assert os.path.exists(output_file)
    cleaned_df = pd.read_pickle(output_file)

    assert cleaned_df.empty
    # Verify that expected columns (including newly derived ones) are present
    assert 'maturity_date' in cleaned_df.columns
    assert 'spread_bps' in cleaned_df.columns
    assert 'nmd_classification' in cleaned_df.columns

def test_preprocess_positions_data_missing_critical_column(temp_dir):
    """
    Test behavior when a critical column (e.g., 'instrument_type' for NMD tagging)
    is missing from the input DataFrame. This should typically raise an error
    as core logic cannot proceed without it.
    """
    # Missing 'instrument_type' which is crucial for NMD tagging
    input_data = {
        'instrument_id': [1, 2],
        # 'instrument_type': missing
        'maturity_date': ['2023-01-15', '2024-01-15'],
        'next_reprice_date': ['2022-07-01', '2023-01-01'],
        'spread_bps': [10.5, None],
        'core_fraction': [0.0, 0.8]
    }
    input_df = pd.DataFrame(input_data)
    output_file = os.path.join(temp_dir, 'missing_cols_clean_positions.pkl')

    # Expecting a KeyError if 'instrument_type' is accessed directly for NMD logic
    with pytest.raises(KeyError, match="'instrument_type'"):
        preprocess_positions_data(input_df, output_file)
    
    # Assert that no output file is created on error
    assert not os.path.exists(output_file)

def test_preprocess_positions_data_invalid_date_formats(temp_dir):
    """
    Test handling of invalid date strings in date columns.
    Expected behavior is to convert them to NaT (Not a Time) without raising an error.
    """
    input_data = {
        'instrument_id': [1, 2, 3],
        'instrument_type': ['Loan', 'Deposit', 'Bond'],
        'maturity_date': ['2023-01-15', 'INVALID_DATE_FORMAT', '2025/12/31'], # Valid, Invalid, Different Valid
        'next_reprice_date': ['2022-07-01', 'ANOTHER_BAD_DATE', None], # Valid, Invalid, None
        'spread_bps': [10.0, 5.0, 2.0],
        'core_fraction': [0.0, 0.0, 0.0]
    }
    input_df = pd.DataFrame(input_data)
    output_file = os.path.join(temp_dir, 'invalid_dates_clean_positions.pkl')

    preprocess_positions_data(input_df, output_file)

    assert os.path.exists(output_file)
    cleaned_df = pd.read_pickle(output_file)

    # Assert that invalid date strings become NaT
    assert pd.isna(cleaned_df.loc[1, 'maturity_date'])
    assert pd.isna(cleaned_df.loc[1, 'next_reprice_date'])
    # Assert that valid but differently formatted dates are parsed
    assert cleaned_df.loc[2, 'maturity_date'] == datetime(2025, 12, 31)
    # Assert that None in date columns becomes NaT
    assert pd.isna(cleaned_df.loc[2, 'next_reprice_date'])
    
    # Ensure columns are still of datetime type even with NaT values
    assert pd.api.types.is_datetime64_any_dtype(cleaned_df['maturity_date'])
    assert pd.api.types.is_datetime64_any_dtype(cleaned_df['next_reprice_date'])

def test_preprocess_positions_data_spread_bps_edge_cases(temp_dir):
    """
    Test `spread_bps` column handling with various non-numeric values and NaNs.
    It should be converted to numeric, and non-numeric/NaN values should be filled with 0.
    """
    input_data = {
        'instrument_id': [1, 2, 3, 4, 5],
        'instrument_type': ['Loan', 'Deposit', 'Bond', 'Loan', 'NMD'],
        'maturity_date': ['2023-01-01'] * 5,
        'next_reprice_date': ['2023-01-01'] * 5,
        'spread_bps': [10.5, None, '5', 'abc', pd.NA], # Mixed types: float, None, string num, string non-num, pd.NA
        'core_fraction': [0.0, 0.0, 0.0, 0.0, 0.5]
    }
    input_df = pd.DataFrame(input_data)
    output_file = os.path.join(temp_dir, 'spread_bps_edge_cases_clean_positions.pkl')

    preprocess_positions_data(input_df, output_file)

    assert os.path.exists(output_file)
    cleaned_df = pd.read_pickle(output_file)

    # Assert spread_bps is numeric after processing
    assert pd.api.types.is_numeric_dtype(cleaned_df['spread_bps'])

    # Assert values are converted and filled correctly
    assert cleaned_df.loc[0, 'spread_bps'] == 10.5
    assert cleaned_df.loc[1, 'spread_bps'] == 0.0 # None should be filled with 0
    assert cleaned_df.loc[2, 'spread_bps'] == 5.0 # '5' (string) should be converted to 5.0 (float)
    assert cleaned_df.loc[3, 'spread_bps'] == 0.0 # 'abc' should become NaN then filled with 0
    assert cleaned_df.loc[4, 'spread_bps'] == 0.0 # pd.NA should be filled with 0