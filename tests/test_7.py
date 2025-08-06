import pytest
from unittest.mock import MagicMock
import pandas as pd
import os

# Placeholder for your module
# Keep the your_module block as it is. DO NOT REPLACE or REMOVE the block.
from definition_a2dee13d174d4e42b99b07e3bad665bb import generate_cash_flows


# Helper for a minimal mock model class
class MockModel:
    def __init__(self, name="GenericModel"):
        self.name = name

    def predict(self, data):
        """Simulates a prediction method if the model is used for inference."""
        # For a stub, this won't be called, but provides a realistic mock object
        return data * 0.5

    def apply_to_dataframe(self, df):
        """Simulates applying the model logic to a DataFrame."""
        if 'notional_amt' in df.columns:
            df[f'cashflow_adj_{self.name.lower()}'] = df['notional_amt'] * 0.001
        return df


@pytest.fixture
def mock_paths(tmp_path):
    """Fixture to create dummy file paths within a temporary directory."""
    cleaned_positions_path = tmp_path / "cleaned_positions.pkl"
    mortgage_model_path = tmp_path / "mortgage_model.pkl"
    nmd_model_path = tmp_path / "nmd_model.pkl"
    output_cashflows_path = tmp_path / "output_cashflows.parquet"

    # Create dummy files to simulate their existence if `os.path.exists` were checked
    # (though we'll patch pandas.read_pickle directly)
    cleaned_positions_path.touch()
    mortgage_model_path.touch()
    nmd_model_path.touch()

    return {
        "cleaned_positions_path": str(cleaned_positions_path),
        "mortgage_model_path": str(mortgage_model_path),
        "nmd_model_path": str(nmd_model_path),
        "output_cashflows_path": str(output_cashflows_path),
    }


def test_generate_cash_flows_success(mocker, mock_paths):
    """
    Test case 1: Happy path - ensures the function executes successfully
    with valid inputs, reading all necessary files and writing the output.
    """
    # Mock input dataframes and model objects
    mock_cleaned_positions_df = pd.DataFrame({
        'instrument_id': [1, 2, 3],
        'notional_amt': [1000, 2500, 5000],
        'instrument_type': ['Mortgage', 'NMD', 'Loan'],
        'maturity_date': pd.to_datetime(['2030-01-01', '2040-01-01', '2025-01-01'])
    })
    mock_mortgage_model = MockModel("MortgagePrepay")
    mock_nmd_model = MockModel("NMD_Beta")

    # Patch pandas.read_pickle to return mocked data/models in order of expected calls
    mock_read_pickle = mocker.patch('pandas.read_pickle', side_effect=[
        mock_cleaned_positions_df,  # First call: cleaned_positions_path
        mock_mortgage_model,        # Second call: mortgage_model_path
        mock_nmd_model              # Third call: nmd_model_path
    ])
    # Patch pandas.DataFrame.to_parquet to capture the output call
    mock_to_parquet = mocker.patch('pandas.DataFrame.to_parquet')

    generate_cash_flows(
        mock_paths["cleaned_positions_path"],
        mock_paths["mortgage_model_path"],
        mock_paths["nmd_model_path"],
        mock_paths["output_cashflows_path"]
    )

    # Assert that read_pickle was called for all expected paths
    mock_read_pickle.assert_any_call(mock_paths["cleaned_positions_path"])
    mock_read_pickle.assert_any_call(mock_paths["mortgage_model_path"])
    mock_read_pickle.assert_any_call(mock_paths["nmd_model_path"])

    # Assert that to_parquet was called exactly once with the correct output path
    mock_to_parquet.assert_called_once_with(mock_paths["output_cashflows_path"])

    # In a real implementation, you'd also assert on the content/structure
    # of the DataFrame passed to to_parquet, e.g.,
    # assert 'simulated_cf' in mock_to_parquet.call_args[0][0].columns


def test_generate_cash_flows_cleaned_positions_file_not_found(mocker, mock_paths):
    """
    Test case 2: Edge case - Cleaned positions file does not exist.
    Expects FileNotFoundError to be raised.
    """
    # Patch pandas.read_pickle to raise FileNotFoundError on the first call
    mock_read_pickle = mocker.patch('pandas.read_pickle', side_effect=FileNotFoundError("Cleaned positions data not found"))
    mock_to_parquet = mocker.patch('pandas.DataFrame.to_parquet')

    with pytest.raises(FileNotFoundError) as excinfo:
        generate_cash_flows(
            mock_paths["cleaned_positions_path"],
            mock_paths["mortgage_model_path"],
            mock_paths["nmd_model_path"],
            mock_paths["output_cashflows_path"]
        )
    assert "Cleaned positions data not found" in str(excinfo.value)
    # Ensure that to_parquet was not called
    mock_to_parquet.assert_not_called()
    # Ensure read_pickle was called for the first path only
    mock_read_pickle.assert_called_once_with(mock_paths["cleaned_positions_path"])


def test_generate_cash_flows_invalid_mortgage_model_format(mocker, mock_paths):
    """
    Test case 3: Edge case - Mortgage model file is corrupt or in an invalid format.
    Expects a relevant error (e.g., TypeError if the loaded object is not callable/usable).
    """
    mock_cleaned_positions_df = pd.DataFrame({'instrument_id': [1], 'notional_amt': [1000]})

    # Patch pandas.read_pickle to successfully load positions, but fail on mortgage model
    # Simulate a scenario where the loaded model is not a valid object, causing a TypeError
    mock_read_pickle = mocker.patch('pandas.read_pickle', side_effect=[
        mock_cleaned_positions_df,  # Cleaned positions loaded successfully
        TypeError("Corrupt or invalid mortgage model object") # Error when loading mortgage model
    ])
    mock_to_parquet = mocker.patch('pandas.DataFrame.to_parquet')

    with pytest.raises(TypeError) as excinfo:
        generate_cash_flows(
            mock_paths["cleaned_positions_path"],
            mock_paths["mortgage_model_path"],
            mock_paths["nmd_model_path"],
            mock_paths["output_cashflows_path"]
        )
    assert "Corrupt or invalid mortgage model object" in str(excinfo.value)
    # Ensure to_parquet was not called
    mock_to_parquet.assert_not_called()
    # Ensure read_pickle was called at least for positions and mortgage model
    mock_read_pickle.assert_any_call(mock_paths["cleaned_positions_path"])
    mock_read_pickle.assert_any_call(mock_paths["mortgage_model_path"])


def test_generate_cash_flows_output_path_permission_denied(mocker, mock_paths):
    """
    Test case 4: Edge case - Output directory lacks write permissions.
    Expects PermissionError or OSError to be raised.
    """
    mock_cleaned_positions_df = pd.DataFrame({
        'instrument_id': [1], 'notional_amt': [1000], 'instrument_type': ['Mortgage']
    })
    mock_mortgage_model = MockModel("MortgagePrepay")
    mock_nmd_model = MockModel("NMD_Beta")

    mock_read_pickle = mocker.patch('pandas.read_pickle', side_effect=[
        mock_cleaned_positions_df,
        mock_mortgage_model,
        mock_nmd_model
    ])
    # Patch pandas.DataFrame.to_parquet to simulate a PermissionError
    mock_to_parquet = mocker.patch('pandas.DataFrame.to_parquet', side_effect=PermissionError("Access denied to output directory"))

    with pytest.raises(PermissionError) as excinfo:
        generate_cash_flows(
            mock_paths["cleaned_positions_path"],
            mock_paths["mortgage_model_path"],
            mock_paths["nmd_model_path"],
            mock_paths["output_cashflows_path"]
        )
    assert "Access denied to output directory" in str(excinfo.value)
    # Ensure all input files were attempted to be read before the write operation failed
    mock_read_pickle.assert_any_call(mock_paths["cleaned_positions_path"])
    mock_read_pickle.assert_any_call(mock_paths["mortgage_model_path"])
    mock_read_pickle.assert_any_call(mock_paths["nmd_model_path"])
    # Ensure to_parquet was called exactly once, leading to the error
    mock_to_parquet.assert_called_once_with(mock_paths["output_cashflows_path"])


def test_generate_cash_flows_empty_positions_data(mocker, mock_paths):
    """
    Test case 5: Edge case - Cleaned positions data is an empty DataFrame.
    Expects the function to handle it gracefully by attempting to write an (empty) Parquet file.
    """
    # Mock cleaned positions as an empty DataFrame
    mock_cleaned_positions_df = pd.DataFrame(columns=[
        'instrument_id', 'notional_amt', 'instrument_type', 'maturity_date'
    ]) # Define columns to simulate expected structure
    mock_mortgage_model = MockModel("MortgagePrepay")
    mock_nmd_model = MockModel("NMD_Beta")

    mock_read_pickle = mocker.patch('pandas.read_pickle', side_effect=[
        mock_cleaned_positions_df,
        mock_mortgage_model,
        mock_nmd_model
    ])
    mock_to_parquet = mocker.patch('pandas.DataFrame.to_parquet')

    generate_cash_flows(
        mock_paths["cleaned_positions_path"],
        mock_paths["mortgage_model_path"],
        mock_paths["nmd_model_path"],
        mock_paths["output_cashflows_path"]
    )

    # Assert that all inputs were read
    mock_read_pickle.assert_any_call(mock_paths["cleaned_positions_path"])
    mock_read_pickle.assert_any_call(mock_paths["mortgage_model_path"])
    mock_read_pickle.assert_any_call(mock_paths["nmd_model_path"])

    # Assert that to_parquet was called, even with empty data
    mock_to_parquet.assert_called_once_with(mock_paths["output_cashflows_path"])

    # If the function were implemented, you'd check the content of the DataFrame
    # passed to to_parquet, e.g., assert mock_to_parquet.call_args[0][0].empty