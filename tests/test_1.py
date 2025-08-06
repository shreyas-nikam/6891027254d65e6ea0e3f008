import pytest
import pandas as pd
import yaml
import io # Required for mocking file content with pandas.read_csv

# This is the placeholder block. DO NOT REPLACE or REMOVE.
from definition_c4faf81461fc40cbbf264ad182c536dd import load_and_preprocess_data

# --- Mock Data Definitions ---

# Mock positions CSV content for a successful load
MOCK_CSV_SUCCESS_CONTENT = """instrument_id,side,notional,rate_type,coupon_or_spread,index,payment_freq,maturity_date,next_reprice_date,currency,embedded_option_flag,core_flag
1,Asset,100000,Fixed,0.05,,Annual,2025-12-31,2024-01-01,TWD,False,False
2,Asset,50000,Floating,0.01,LIBOR,Monthly,2026-06-30,2024-01-15,TWD,False,False
3,Liability,20000,NMD,0.005,,Monthly,,2024-01-01,TWD,False,True
4,Asset,75000,Fixed,0.04,,Monthly,2030-01-01,2024-01-01,TWD,True,False
5,Asset,10000,Non-Interest,,,Monthly,2025-01-01,2024-01-01,TWD,False,False
"""

# Mock positions CSV content with a missing mandatory column (e.g., 'notional')
# This will likely cause a KeyError or ValueError when the function tries to
# access this column for filtering or processing.
MOCK_CSV_MISSING_COL_CONTENT = """instrument_id,side,rate_type,coupon_or_spread,index,payment_freq,maturity_date,next_reprice_date,currency,embedded_option_flag,core_flag
1,Asset,Fixed,0.05,,Annual,2025-12-31,2024-01-01,TWD,False,False
"""

# Mock empty positions CSV content
MOCK_CSV_EMPTY_CONTENT = ""

# Mock assumptions YAML content for a successful load
MOCK_YAML_SUCCESS_CONTENT = """
behavioral_overlays:
  mortgage_prepayment_rate_annual: 0.05
  nmd_beta: 0.5
"""

@pytest.mark.parametrize(
    "file_path, assumptions_path, mock_csv_data, mock_yaml_data, csv_read_exception, yaml_load_exception, expected_exception_type",
    [
        # Test Case 1: Happy Path - Valid Inputs
        # Expects a pandas DataFrame as output after successful processing.
        (
            "data/positions.csv", "config/assumptions.yaml",
            MOCK_CSV_SUCCESS_CONTENT, MOCK_YAML_SUCCESS_CONTENT,
            None, None,
            None # No exception expected, should return DataFrame
        ),
        # Test Case 2: Positions CSV File Not Found
        # Expects FileNotFoundError if the positions file is missing.
        (
            "data/non_existent_positions.csv", "config/assumptions.yaml",
            None, MOCK_YAML_SUCCESS_CONTENT,
            FileNotFoundError, None,
            FileNotFoundError
        ),
        # Test Case 3: Assumptions YAML File Not Found
        # Expects FileNotFoundError if the assumptions YAML file is missing.
        (
            "data/positions.csv", "config/non_existent_assumptions.yaml",
            MOCK_CSV_SUCCESS_CONTENT, None,
            None, FileNotFoundError,
            FileNotFoundError
        ),
        # Test Case 4: Empty Positions CSV File
        # Expects a DataFrame (likely empty) after processing an empty input CSV.
        (
            "data/empty_positions.csv", "config/assumptions.yaml",
            MOCK_CSV_EMPTY_CONTENT, MOCK_YAML_SUCCESS_CONTENT,
            None, None,
            None # Should return a DataFrame, potentially empty
        ),
        # Test Case 5: Positions CSV with Missing Mandatory Column
        # Expects a KeyError if the internal logic attempts to access a missing column
        # like 'notional' which is crucial for processing.
        (
            "data/malformed_positions.csv", "config/assumptions.yaml",
            MOCK_CSV_MISSING_COL_CONTENT, MOCK_YAML_SUCCESS_CONTENT,
            None, None,
            KeyError # Assuming 'notional' or similar is accessed directly
        ),
    ]
)
def test_load_and_preprocess_data(
    mocker,
    file_path, assumptions_path,
    mock_csv_data, mock_yaml_data,
    csv_read_exception, yaml_load_exception,
    expected_exception_type
):
    """
    Test cases for load_and_preprocess_data function covering various scenarios.
    Mocks file I/O operations and asserts expected behavior or exceptions.
    """
    # Mock pandas.read_csv to control CSV file content or raise exceptions
    mock_read_csv = mocker.patch('pandas.read_csv')
    if csv_read_exception:
        mock_read_csv.side_effect = csv_read_exception
    elif mock_csv_data is not None:
        if mock_csv_data == MOCK_CSV_EMPTY_CONTENT:
            # For empty CSV, return a DataFrame with expected columns but no rows
            # These columns are based on the specification's "Mandatory Columns"
            mock_read_csv.return_value = pd.DataFrame(columns=[
                'instrument_id', 'side', 'notional', 'rate_type', 'coupon_or_spread',
                'index', 'payment_freq', 'maturity_date', 'next_reprice_date',
                'currency', 'embedded_option_flag', 'core_flag'
            ])
        else:
            # For other CSV content, use StringIO to parse it into a DataFrame
            mock_read_csv.return_value = pd.read_csv(io.StringIO(mock_csv_data))
    
    # Mock yaml.safe_load to control YAML content or raise exceptions
    mock_safe_load = mocker.patch('yaml.safe_load')
    if yaml_load_exception:
        mock_safe_load.side_effect = yaml_load_exception
    elif mock_yaml_data is not None:
        mock_safe_load.return_value = yaml.safe_load(mock_yaml_data)
    
    # Mock builtins.open for the YAML file path, as load_and_preprocess_data
    # likely uses open() before passing to yaml.safe_load()
    if yaml_load_exception == FileNotFoundError:
        mocker.patch('builtins.open', side_effect=FileNotFoundError)
    elif mock_yaml_data is not None:
        # For valid YAML data, provide a mock_open object
        mocker.patch('builtins.open', mocker.mock_open(read_data=mock_yaml_data))

    if expected_exception_type:
        # Test case expects an exception
        with pytest.raises(expected_exception_type):
            load_and_preprocess_data(file_path, assumptions_path)
    else:
        # Test case expects a successful execution (Happy Path or Empty CSV)
        result = load_and_preprocess_data(file_path, assumptions_path)
        
        # NOTE: The actual 'load_and_preprocess_data' function stub provided
        # contains 'pass', meaning it currently returns 'None'.
        # These assertions below are written expecting the function to be
        # fully implemented as per its docstring (returning a DataFrame).
        # Therefore, these assertions WILL FAIL against the current 'pass' stub,
        # but will pass once the function is correctly implemented.
        # This aligns with the example output's implicit expectation for the sum function.
        
        assert isinstance(result, pd.DataFrame) 
        
        if file_path == "data/positions.csv":
            # For a successful, non-empty input, expect a non-empty DataFrame
            assert not result.empty
            # Expected columns after processing (assumed based on "expanded monthly cash flows")
            expected_output_cols = ['instrument_id', 'cashflow_date', 'principal_cf', 'interest_cf', 'side']
            assert all(col in result.columns for col in expected_output_cols)
            # Assert that the non-interest-sensitive asset (instrument_id 5 from MOCK_CSV_SUCCESS_CONTENT) is filtered out
            assert 5 not in result['instrument_id'].unique()
            # Assert that other interest-sensitive instruments are still present
            assert 1 in result['instrument_id'].unique()
            assert 2 in result['instrument_id'].unique()
            assert 3 in result['instrument_id'].unique()
            assert 4 in result['instrument_id'].unique()

        elif file_path == "data/empty_positions.csv":
            # For an empty input, expect an empty DataFrame
            assert result.empty
            # It should still have the expected columns after processing, even if empty
            expected_output_cols = ['instrument_id', 'cashflow_date', 'principal_cf', 'interest_cf', 'side']
            assert all(col in result.columns for col in expected_output_cols)