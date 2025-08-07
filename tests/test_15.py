import pytest
import pandas as pd
from unittest.mock import MagicMock
from definition_d0bf928a49fd4828bfe9bbd1eb44b02b import save_data_to_parquet

@pytest.fixture
def sample_dataframe():
    """Returns a sample pandas DataFrame for testing."""
    return pd.DataFrame({'id': [1, 2, 3], 'value': [100.5, 200.75, 300.0]})

@pytest.fixture
def empty_dataframe():
    """Returns an empty pandas DataFrame for testing."""
    return pd.DataFrame({'id': [], 'value': []})

def test_save_data_to_parquet_successful(tmp_path, sample_dataframe, mocker):
    """
    Test case 1: Verifies that save_data_to_parquet successfully calls
    DataFrame.to_parquet with the correct arguments for a valid DataFrame.
    """
    mock_to_parquet = mocker.patch.object(pd.DataFrame, 'to_parquet', autospec=True)
    filepath = tmp_path / "gap_table.parquet"

    save_data_to_parquet(sample_dataframe, str(filepath))

    # Assert that the to_parquet method was called exactly once on the DataFrame
    # Note: `index=False` is a common and often expected argument when saving to Parquet,
    # as Pandas DataFrame indices are usually not stored directly in Parquet files unless specified.
    # The exact arguments depend on the implementation of save_data_to_parquet.
    # We assume a standard use where index is not written to Parquet.
    mock_to_parquet.assert_called_once_with(sample_dataframe, str(filepath), index=False)

def test_save_data_to_parquet_empty_dataframe(tmp_path, empty_dataframe, mocker):
    """
    Test case 2: Verifies that save_data_to_parquet handles an empty DataFrame
    correctly by calling DataFrame.to_parquet. Parquet can store empty data.
    """
    mock_to_parquet = mocker.patch.object(pd.DataFrame, 'to_parquet', autospec=True)
    filepath = tmp_path / "empty_table.parquet"

    save_data_to_parquet(empty_dataframe, str(filepath))

    mock_to_parquet.assert_called_once_with(empty_dataframe, str(filepath), index=False)

def test_save_data_to_parquet_invalid_dataframe_type(tmp_path):
    """
    Test case 3: Verifies that a TypeError is raised when the 'dataframe' argument
    is not a pandas DataFrame, as specified in the docstring.
    """
    filepath = tmp_path / "invalid_type.parquet"
    
    with pytest.raises(TypeError):
        save_data_to_parquet([1, 2, 3], str(filepath)) # List instead of DataFrame
    with pytest.raises(TypeError):
        save_data_to_parquet(None, str(filepath))     # None instead of DataFrame

def test_save_data_to_parquet_invalid_filename_type(sample_dataframe):
    """
    Test case 4: Verifies that a TypeError is raised when the 'filename' argument
    is not a string, as specified in the docstring.
    """
    with pytest.raises(TypeError):
        save_data_to_parquet(sample_dataframe, 12345)  # Integer instead of string
    with pytest.raises(TypeError):
        save_data_to_parquet(sample_dataframe, None)   # None instead of string

def test_save_data_to_parquet_io_error_during_save(tmp_path, sample_dataframe, mocker):
    """
    Test case 5: Simulates an IOError during the saving process (e.g., due to
    disk full, permissions, or invalid path) and verifies that it is propagated.
    """
    mock_to_parquet = mocker.patch.object(pd.DataFrame, 'to_parquet', 
                                          side_effect=IOError("Simulated disk full error"),
                                          autospec=True)
    filepath = tmp_path / "problem_table.parquet"

    with pytest.raises(IOError, match="Simulated disk full error"):
        save_data_to_parquet(sample_dataframe, str(filepath))

    # Ensure the saving attempt was made
    mock_to_parquet.assert_called_once_with(sample_dataframe, str(filepath), index=False)