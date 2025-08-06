import pytest
import pandas as pd
import os
import pickle
from unittest.mock import MagicMock

# Keep a placeholder definition_a937abeb957b402ab962b10e418a122a for the import of the module.
# Keep the `your_module` block as it is. DO NOT REPLACE or REMOVE the block.
from definition_a937abeb957b402ab962b10e418a122a import calibrate_nmd_beta_model

# Helper to create dummy data for mocking
def create_dummy_nmd_data():
    """Returns a pandas DataFrame with suitable data for NMD beta calibration."""
    return pd.DataFrame({
        'policy_rate': [0.01, 0.015, 0.02, 0.025, 0.03],
        'deposit_rate': [0.005, 0.007, 0.009, 0.011, 0.013],
        'timestamp': pd.to_datetime(['2023-01-01', '2023-02-01', '2023-03-01', '2023-04-01', '2023-05-01'])
    })

# Fixture to provide basic mocks for pandas I/O and pickle dumping
@pytest.fixture
def mock_io(mocker):
    """Mocks pandas.read_pickle and pickle.dump."""
    mocker.patch('pandas.read_pickle', return_value=create_dummy_nmd_data())
    mocker.patch('pickle.dump') # For saving the model

def test_successful_calibration(tmp_path, mock_io):
    """
    Test case 1: Ensures the function processes valid input data and attempts to save the model.
    This test verifies the 'happy path' by checking mock calls.
    """
    cleaned_data_path = tmp_path / "mock_cleaned_data.pkl"
    model_output_path = tmp_path / "mock_nmd_beta_model.pkl"

    # Call the function (the stub, whose expected behavior is simulated by mocks)
    calibrate_nmd_beta_model(str(cleaned_data_path), str(model_output_path))

    # Assert that data was attempted to be read
    pd.read_pickle.assert_called_once_with(str(cleaned_data_path))

    # Assert that the model was attempted to be saved
    pickle.dump.assert_called_once()
    # Verify the second argument of pickle.dump (the file handle's name attribute)
    # The first argument is the model object, which is a mock here.
    assert pickle.dump.call_args[0][1].name == str(model_output_path)


def test_cleaned_data_path_non_existent(mocker):
    """
    Test case 2: Verifies that a FileNotFoundError is handled if cleaned_data_path does not exist.
    Mocks pandas.read_pickle to simulate this file system error.
    """
    non_existent_path = "/non_existent_dir/non_existent_file.pkl"
    model_output_path = "/tmp/some_model.pkl"

    # Mock pandas.read_pickle to raise FileNotFoundError when called
    mocker.patch('pandas.read_pickle', side_effect=FileNotFoundError(f"No such file or directory: '{non_existent_path}'"))

    with pytest.raises(FileNotFoundError) as excinfo:
        calibrate_nmd_beta_model(non_existent_path, model_output_path)

    assert f"No such file or directory: '{non_existent_path}'" in str(excinfo.value)
    pd.read_pickle.assert_called_once_with(non_existent_path)


def test_invalid_cleaned_data_format_for_calibration(mocker):
    """
    Test case 3: Checks for expected errors (KeyError/ValueError) if the cleaned data
    lacks necessary columns for NMD beta model calibration (e.g., 'policy_rate').
    Mocks pandas.read_pickle to return a malformed DataFrame and then simulates internal logic failure.
    """
    cleaned_data_path = "/path/to/malformed_data.pkl"
    model_output_path = "/tmp/some_model.pkl"

    # Create a mock DataFrame object whose __getitem__ method simulates a KeyError
    # when trying to access 'policy_rate' or 'deposit_rate'
    mock_df_instance = MagicMock()
    # Using a side_effect function to raise KeyError only for specific keys
    mock_df_instance.__getitem__.side_effect = lambda key: KeyError(f"Column '{key}' not found.") \
        if key in ['policy_rate', 'deposit_rate'] else MagicMock() # Return a generic mock for other accesses
    
    mocker.patch('pandas.read_pickle', return_value=mock_df_instance)
    # Also mock pickle.dump so that if the function proceeds, it doesn't fail on saving
    mocker.patch('pickle.dump')

    with pytest.raises(KeyError) as excinfo: # Or ValueError, depending on implementation detail
        calibrate_nmd_beta_model(cleaned_data_path, model_output_path)

    # The specific message depends on which column is accessed first.
    assert "Column 'policy_rate' not found." in str(excinfo.value) or \
           "Column 'deposit_rate' not found." in str(excinfo.value)
    pd.read_pickle.assert_called_once_with(cleaned_data_path)


def test_model_output_path_permission_denied(tmp_path, mock_io, mocker):
    """
    Test case 4: Verifies that a PermissionError is raised if the function cannot write
    to the specified model_output_path due to permissions.
    Mocks pickle.dump to simulate this file system error.
    """
    cleaned_data_path = tmp_path / "mock_cleaned_data.pkl"
    # A generic path that would typically cause permission issues if not mocked
    restricted_output_path = "/dev/null/restricted_output.pkl" 

    # Mock pickle.dump to raise PermissionError when called
    mocker.patch('pickle.dump', side_effect=PermissionError(f"Permission denied: '{restricted_output_path}'"))

    with pytest.raises(PermissionError) as excinfo:
        calibrate_nmd_beta_model(str(cleaned_data_path), restricted_output_path)

    assert f"Permission denied: '{restricted_output_path}'" in str(excinfo.value)
    pd.read_pickle.assert_called_once_with(str(cleaned_data_path))
    pickle.dump.assert_called_once() # Should be called once before raising the error


@pytest.mark.parametrize("cleaned_data_arg, model_output_arg", [
    (123, "output.pkl"),          # cleaned_data_path is not string
    ("input.pkl", None),          # model_output_path is not string
    (None, "output.pkl"),         # cleaned_data_path is None
    (123, 456),                   # Both are not strings
])
def test_invalid_path_types(cleaned_data_arg, model_output_arg, mocker):
    """
    Test case 5: Ensures TypeError is raised when path arguments are not strings.
    This relies on underlying library calls (like pandas.read_pickle or built-in open)
    to raise a TypeError if a non-string path is passed.
    """
    # Mock core I/O functions that would be called by pandas or pickle,
    # and would naturally raise TypeError for non-string paths.
    # We do NOT mock calibrate_nmd_beta_model itself.
    mocker.patch('pandas.read_pickle', side_effect=TypeError("Expected str, bytes or os.PathLike object, not int"))
    mocker.patch('pickle.dump', side_effect=TypeError("Expected str, bytes or os.PathLike object, not NoneType"))

    with pytest.raises(TypeError) as excinfo:
        calibrate_nmd_beta_model(cleaned_data_arg, model_output_arg)
    
    # Assert that the error message indicates a type mismatch for a path-like object.
    # The exact message can vary by Python/library version.
    assert any(msg in str(excinfo.value) for msg in [
        "Expected str, bytes or os.PathLike object",
        "Path-like object expected",
        "must be a string or PathLike object",
        "not a string, bytes or os.PathLike object"
    ])