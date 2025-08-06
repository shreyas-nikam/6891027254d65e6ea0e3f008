import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

# Keep a placeholder definition_7ce6c523963c480d845040a92530b471 for the import of the module.
# Keep the `your_module` block as it is. DO NOT REPLACE or REMOVE the block.
from definition_7ce6c523963c480d845040a92530b471 import generate_gap_table

# Define Basel buckets as per the specification. In a real scenario, this would
# likely be an internal constant or derived within the `generate_gap_table`
# function itself. For testing purposes, we use a fixed list to assert against.
BASEL_BUCKETS = [
    "0-1 Month", "1-3 Months", "3-6 Months", "6-12 Months",
    "1-2 Years", "2-3 Years", "3-5 Years", "5-10 Years", "Over 10 Years"
]

@pytest.fixture
def mock_cashflows_data():
    """
    Provides a sample DataFrame that simulates the content of
    'irrbb_taiwan_cashflows_long.parquet'.
    This mock data includes dates, amounts, and types necessary for bucketing
    and calculating inflows/outflows. PV01 calculation is assumed to be
    handled internally by generate_gap_table.
    """
    data = {
        'date': pd.to_datetime([
            '2023-01-15', '2023-02-01', '2023-04-20', '2023-07-01', 
            '2024-06-01', '2025-01-01', '2027-03-01', '2030-05-01', '2035-01-01', # Inflow dates
            '2023-01-20', '2023-03-01', '2023-05-10', '2023-09-01', 
            '2024-11-01', '2026-02-01', '2028-04-01', '2032-06-01', '2040-01-01'  # Outflow dates
        ]),
        'amount': [
            1000, 2000, 1500, 500, 3000, 2500, 4000, 6000, 8000, # Inflow amounts
            500, 1000, 750, 250, 1500, 1250, 2000, 3000, 4000  # Outflow amounts
        ],
        'type': [
            'inflow', 'inflow', 'inflow', 'inflow', 'inflow', 'inflow', 'inflow', 'inflow', 'inflow',
            'outflow', 'outflow', 'outflow', 'outflow', 'outflow', 'outflow', 'outflow', 'outflow', 'outflow'
        ]
    }
    return pd.DataFrame(data)

@patch('pandas.read_parquet')
@patch('pandas.DataFrame.to_csv')
def test_generate_gap_table_success(mock_to_csv, mock_read_parquet, mock_cashflows_data):
    """
    Test case 1: Happy Path - Verifies the function correctly reads input,
    processes, returns a DataFrame with the expected structure, and saves to CSV.
    It asserts the presence of required columns and correct indexing.
    """
    mock_read_parquet.return_value = mock_cashflows_data
    cashflows_path = "dummy_cashflows.parquet"
    output_gap_table_path = "dummy_gap_table.csv"

    # Call the function under test
    result_df = generate_gap_table(cashflows_path, output_gap_table_path)

    # Assert that pandas.read_parquet was called with the correct path
    mock_read_parquet.assert_called_once_with(cashflows_path)
    
    # Assert that DataFrame.to_csv was called on the result with the correct path
    # and that the index was preserved (as buckets are the index)
    mock_to_csv.assert_called_once_with(output_gap_table_path, index=True) 

    # Assert the returned object is a pandas DataFrame
    assert isinstance(result_df, pd.DataFrame)
    # Assert the DataFrame is not empty (contains bucket rows)
    assert not result_df.empty
    # Assert the DataFrame's index matches the expected Basel buckets
    assert list(result_df.index) == BASEL_BUCKETS
    # Assert all required output columns are present
    assert all(col in result_df.columns for col in ['Inflows', 'Outflows', 'Net Gap', 'Partial PV01'])
    # Assert that calculations resulted in non-zero values (assuming non-empty input)
    assert result_df['Net Gap'].sum() != 0
    assert result_df['Partial PV01'].sum() != 0

@patch('pandas.read_parquet')
@patch('pandas.DataFrame.to_csv')
def test_generate_gap_table_empty_cashflows(mock_to_csv, mock_read_parquet):
    """
    Test case 2: Edge Case - Verifies function behavior when the input cashflows file is empty.
    It should still produce a gap table with the correct structure, but all value columns
    should contain zeros.
    """
    # Mock read_parquet to return an empty DataFrame with expected columns
    mock_read_parquet.return_value = pd.DataFrame(columns=['date', 'amount', 'type'])
    cashflows_path = "empty_cashflows.parquet"
    output_gap_table_path = "empty_gap_table.csv"

    # Call the function
    result_df = generate_gap_table(cashflows_path, output_gap_table_path)

    # Assert I/O calls
    mock_read_parquet.assert_called_once_with(cashflows_path)
    mock_to_csv.assert_called_once_with(output_gap_table_path, index=True)

    # Assert structure
    assert isinstance(result_df, pd.DataFrame)
    assert not result_df.empty # Still contains bucket rows
    assert list(result_df.index) == BASEL_BUCKETS
    assert all(col in result_df.columns for col in ['Inflows', 'Outflows', 'Net Gap', 'Partial PV01'])

    # Assert values are all zeros for empty input
    expected_zero_series = pd.Series([0.0]*len(BASEL_BUCKETS), index=BASEL_BUCKETS, dtype=float)
    pd.testing.assert_series_equal(result_df['Inflows'], expected_zero_series)
    pd.testing.assert_series_equal(result_df['Outflows'], expected_zero_series)
    pd.testing.assert_series_equal(result_df['Net Gap'], expected_zero_series)
    pd.testing.assert_series_equal(result_df['Partial PV01'], expected_zero_series)

@patch('pandas.read_parquet')
def test_generate_gap_table_cashflows_file_not_found(mock_read_parquet):
    """
    Test case 3: Edge Case - Verifies that a FileNotFoundError is raised
    when the specified cashflows_path does not exist.
    """
    # Configure mock read_parquet to raise FileNotFoundError
    mock_read_parquet.side_effect = FileNotFoundError("The specified cashflows file was not found.")
    cashflows_path = "non_existent_cashflows.parquet"
    output_gap_table_path = "dummy_gap_table.csv"

    # Assert that calling the function raises the expected error
    with pytest.raises(FileNotFoundError) as excinfo:
        generate_gap_table(cashflows_path, output_gap_table_path)

    # Assert read_parquet was called with the problematic path
    mock_read_parquet.assert_called_once_with(cashflows_path)
    # Assert the error message contains the expected text
    assert "cashflows file was not found" in str(excinfo.value)

@patch('pandas.read_parquet')
@patch('pandas.DataFrame.to_csv')
def test_generate_gap_table_output_write_error(mock_to_csv, mock_read_parquet, mock_cashflows_data):
    """
    Test case 4: Edge Case - Verifies that an IOError is propagated
    if there is an issue writing the output gap table CSV (e.g., permission denied, invalid path).
    """
    # Mock read_parquet to return valid data
    mock_read_parquet.return_value = mock_cashflows_data
    # Configure mock to_csv to raise an IOError
    mock_to_csv.side_effect = IOError("Permission denied to write to output path.")
    
    cashflows_path = "dummy_cashflows.parquet"
    output_gap_table_path = "/non_writable_directory/output_gap_table.csv"

    # Assert that calling the function raises the expected error
    with pytest.raises(IOError) as excinfo:
        generate_gap_table(cashflows_path, output_gap_table_path)

    # Assert read_parquet was called successfully
    mock_read_parquet.assert_called_once_with(cashflows_path)
    # Assert to_csv was attempted with the problematic path
    mock_to_csv.assert_called_once_with(output_gap_table_path, index=True)
    # Assert the error message contains the expected text
    assert "Permission denied to write to output path." in str(excinfo.value)

@patch('pandas.read_parquet')
@patch('pandas.DataFrame.to_csv')
def test_generate_gap_table_invalid_input_type_path(mock_to_csv, mock_read_parquet):
    """
    Test case 5: Edge Case - Verifies that TypeError is raised when input paths
    are not strings, as expected for robust function arguments.
    """
    # Test cashflows_path as an integer (non-string)
    with pytest.raises(TypeError) as excinfo:
        generate_gap_table(12345, "output.csv")
    assert "cashflows_path must be a string" in str(excinfo.value)

    # Test output_gap_table_path as None (non-string)
    with pytest.raises(TypeError) as excinfo:
        generate_gap_table("input.parquet", None)
    assert "output_gap_table_path must be a string" in str(excinfo.value)

    # Ensure no file operations were attempted for invalid input types
    mock_read_parquet.assert_not_called()
    mock_to_csv.assert_not_called()