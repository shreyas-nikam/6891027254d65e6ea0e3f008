import pytest
import os
import pandas as pd
import shutil

# Make sure to replace definition_3242f8b6ea36491ab725145f42d4b166 with the actual module name when running tests
from definition_3242f8b6ea36491ab725145f42d4b166 import generate_taiwan_portfolio

@pytest.fixture(autouse=True)
def manage_test_environment(tmp_path):
    """
    Sets up a temporary directory for each test, changes the current working
    directory to this temporary path, and ensures the 'data' subdirectory
    is clean if it exists from previous implicit creation.
    It also reverts the CWD after the test.
    """
    original_cwd = os.getcwd()
    os.chdir(tmp_path) # Change CWD to the temporary path for the test run

    # Ensure a clean 'data' directory at the start of each test (if it was created implicitly)
    data_dir = tmp_path / "data"
    if data_dir.exists():
        shutil.rmtree(data_dir) # Remove if exists to ensure clean state
    
    yield tmp_path # Yield the base temporary path

    # Teardown: Revert CWD
    os.chdir(original_cwd)

def test_file_creation_on_first_call(tmp_path):
    """
    Test that the taiwan_bankbook_positions.csv file is created when it does not exist.
    """
    file_path = tmp_path / "data" / "taiwan_bankbook_positions.csv"

    # Pre-condition: file does not exist
    assert not file_path.exists()

    # Call the function
    generate_taiwan_portfolio()

    # Assertion: file should now exist
    assert file_path.exists()

def test_file_contains_expected_structure_and_data(tmp_path):
    """
    Test that the created CSV file has expected columns and contains some data.
    """
    file_path = tmp_path / "data" / "taiwan_bankbook_positions.csv"

    generate_taiwan_portfolio() # Create the file

    assert file_path.exists()

    # Read the CSV and check its structure
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        pytest.fail(f"Could not read the generated CSV file: {e}")

    # Check if DataFrame is not empty and has rows
    assert not df.empty, "The generated CSV file is empty."
    assert len(df) > 0, "The generated CSV file has no rows."

    # Check for presence of mandatory columns as per specification in section 3.2.1
    expected_columns = [
        'instrument_id', 'side', 'notional', 'rate_type', 'coupon_or_spread',
        'index', 'payment_freq', 'maturity_date', 'next_reprice_date',
        'currency', 'embedded_option_flag', 'core_flag'
    ]
    for col in expected_columns:
        assert col in df.columns, f"Missing expected column: {col}"

def test_idempotency_file_exists_and_is_valid_after_recreation(tmp_path):
    """
    Test that calling the function when the file already exists leads to a valid file.
    This implies an overwrite or re-generation to ensure validity.
    """
    file_path = tmp_path / "data" / "taiwan_bankbook_positions.csv"
    data_dir = tmp_path / "data"
    data_dir.mkdir() # Explicitly create data dir for this test's setup

    # Create an initial dummy file with distinct content
    dummy_content = "dummy_col1,dummy_col2\n1,abc\n"
    with open(file_path, "w") as f:
        f.write(dummy_content)
    
    # Call the function again
    generate_taiwan_portfolio()

    # Assert that the file still exists
    assert file_path.exists()

    # Check that the file content is now different from the dummy content
    # and contains the expected generated structure, implying an overwrite.
    df = pd.read_csv(file_path)
    assert not df.empty, "The file became empty after re-running generate_taiwan_portfolio."
    assert len(df) > 0, "The file has no rows after re-running generate_taiwan_portfolio."
    
    # Re-checking mandatory columns to ensure it's a valid generated file, not the dummy.
    expected_columns = [
        'instrument_id', 'side', 'notional', 'rate_type', 'coupon_or_spread',
        'index', 'payment_freq', 'maturity_date', 'next_reprice_date',
        'currency', 'embedded_option_flag', 'core_flag'
    ]
    for col in expected_columns:
        assert col in df.columns, f"Missing expected column: {col} after re-run."
    
    # Ensure it's not the dummy content (e.g., check for dummy_col1 presence)
    assert 'dummy_col1' not in df.columns, "The file was not overwritten with new data."


def test_function_returns_none(tmp_path):
    """
    Test that the generate_taiwan_portfolio function returns None.
    """
    # Call the function and capture its return value
    result = generate_taiwan_portfolio()

    # Assertion: The function should return None
    assert result is None, f"Expected return value to be None, but got {result}"

def test_creates_data_directory_if_not_exists(tmp_path):
    """
    Test that the function creates the 'data' directory if it doesn't exist,
    and then successfully creates the CSV file within it.
    """
    data_dir = tmp_path / "data"
    file_path = data_dir / "taiwan_bankbook_positions.csv"
    
    # Pre-condition: 'data' directory and file do not exist
    assert not data_dir.exists() 
    assert not file_path.exists() 

    # Call the function
    generate_taiwan_portfolio()

    # Assertions: data directory and file should now exist
    assert data_dir.exists()
    assert file_path.exists()

    # Basic check on file content to ensure it's a valid creation
    df = pd.read_csv(file_path)
    assert not df.empty
    assert len(df) > 0