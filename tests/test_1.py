import pytest
import pandas as pd
import os
from definition_dcf6180cd15c4a56a4d3b3e2e59f6368 import load_positions_data

# Test 1: Successful load of a well-formed CSV file
def test_load_positions_data_success(tmp_path):
    """
    Tests if the function correctly loads a valid CSV file into a pandas DataFrame,
    verifying its type, shape, and content.
    """
    file_content = """instrument_id,instrument_type,notional_amt,maturity_date,currency
1,Loan,100000,2025-01-01,TWD
2,Deposit,50000,2024-06-30,TWD
3,Bond,200000,2030-12-31,TWD
"""
    file_path = tmp_path / "irrbb_test_positions.csv"
    file_path.write_text(file_content)

    df = load_positions_data(str(file_path))

    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert df.shape == (3, 5)
    assert df.loc[0, 'notional_amt'] == 100000
    assert df.loc[2, 'instrument_type'] == 'Bond'
    assert df.columns.tolist() == ['instrument_id', 'instrument_type', 'notional_amt', 'maturity_date', 'currency']

# Test 2: Handles a non-existent file path
def test_load_positions_data_file_not_found():
    """
    Tests that a FileNotFoundError is raised when the specified file path does not exist.
    """
    non_existent_path = "non_existent_data.csv"
    with pytest.raises(FileNotFoundError):
        load_positions_data(non_existent_path)

# Test 3: Handles a completely empty CSV file (no headers, no data)
def test_load_positions_data_empty_file_no_headers(tmp_path):
    """
    Tests that pandas.errors.EmptyDataError is raised when the CSV file is completely empty,
    as pd.read_csv expects at least headers or some data.
    """
    empty_file_path = tmp_path / "empty_no_headers.csv"
    empty_file_path.write_text("")

    with pytest.raises(pd.errors.EmptyDataError):
        load_positions_data(str(empty_file_path))

# Test 4: Handles a CSV file containing only headers, but no data rows
def test_load_positions_data_headers_only(tmp_path):
    """
    Tests that the function returns an empty DataFrame with the correct columns
    when the CSV file contains only headers but no data rows.
    """
    headers_only_content = "instrument_id,instrument_type,notional_amt,maturity_date\n"
    headers_only_file_path = tmp_path / "headers_only.csv"
    headers_only_file_path.write_text(headers_only_content)

    df = load_positions_data(str(headers_only_file_path))

    assert isinstance(df, pd.DataFrame)
    assert df.empty  # The DataFrame should be empty of rows
    assert df.columns.tolist() == ['instrument_id', 'instrument_type', 'notional_amt', 'maturity_date']

# Test 5: Handles a malformed CSV file (e.g., inconsistent number of columns)
def test_load_positions_data_malformed_csv(tmp_path):
    """
    Tests that a pandas.errors.ParserError is raised for a malformed CSV file
    where rows have an inconsistent number of columns.
    """
    malformed_content = """instrument_id,instrument_type,notional_amt
1,Loan,100000
2,Deposit # This row is missing a column
"""
    malformed_file_path = tmp_path / "malformed.csv"
    malformed_file_path.write_text(malformed_content)

    with pytest.raises(pd.errors.ParserError):
        load_positions_data(str(malformed_file_path))