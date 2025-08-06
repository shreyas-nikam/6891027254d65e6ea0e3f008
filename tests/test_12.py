import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Placeholder for your module import
# DO NOT REPLACE or REMOVE THE BLOCK
from definition_7dd1f308a5be45f0940db67c6687848a import calculate_irrbb_valuation
# END OF BLOCK

# Mock YieldCurve object, assuming it's a simple class with no complex methods for this test scope
class MockYieldCurve:
    def __init__(self, name="GenericYieldCurve"):
        self.name = name
    def __repr__(self):
        return f"<{self.name}>"

# Base arguments for the function, using Path objects for consistency with mocking
# Paths will be converted to strings right before calling the function, as specified in the signature
base_args_template = {
    "cleaned_positions_path": Path("dummy_cleaned.pkl"),
    "cashflows_path": Path("dummy_cashflows.parquet"),
    "baseline_yield_curve": MockYieldCurve("Baseline"),
    "scenario_yield_curves": {
        "parallel_up": MockYieldCurve("Scenario_ParallelUp"),
        "parallel_down": MockYieldCurve("Scenario_ParallelDown"),
    },
    "mortgage_model_path": Path("dummy_mortgage_model.pkl"),
    "nmd_model_path": Path("dummy_nmd_model.pkl"),
    "eve_baseline_output_path": Path("dummy_eve_baseline.pkl"),
    "eve_scenarios_output_path": Path("dummy_eve_scenarios.pkl"),
    "nii_results_output_path": Path("dummy_nii_results.pkl"),
}

@pytest.mark.parametrize(
    "test_id, args_modifier, mock_path_exists_side_effect, expected_output",
    [
        # Test Case 1: Successful execution - all inputs valid, files exist, outputs are written
        (
            "success_valid_inputs",
            lambda args: args,  # No modification
            lambda p: True,  # All mocked paths exist
            None,  # Expected return value for success
        ),
        # Test Case 2: Input `cleaned_positions_path` file not found
        (
            "fail_cleaned_positions_path_not_found",
            lambda args: args,
            lambda p: p != base_args_template["cleaned_positions_path"],  # cleaned_positions_path does not exist
            FileNotFoundError,
        ),
        # Test Case 3: Invalid `baseline_yield_curve` type
        (
            "fail_invalid_baseline_yield_curve_type",
            lambda args: {**args, "baseline_yield_curve": "not_a_yield_curve_object"},
            lambda p: True,  # All mocked paths exist
            TypeError,
        ),
        # Test Case 4: Empty `scenario_yield_curves` dictionary
        (
            "fail_empty_scenario_yield_curves",
            lambda args: {**args, "scenario_yield_curves": {}},
            lambda p: True,  # All mocked paths exist
            ValueError,
        ),
        # Test Case 5: `mortgage_model_path` file not found
        (
            "fail_mortgage_model_path_not_found",
            lambda args: args,
            lambda p: p != base_args_template["mortgage_model_path"],  # mortgage_model_path does not exist
            FileNotFoundError,
        ),
    ]
)
@patch('pathlib.Path.exists') # Mock Path.exists to control file existence
@patch('builtins.open')      # Mock open to simulate file writing
def test_calculate_irrbb_valuation(
    mock_open, mock_path_exists, test_id, args_modifier, mock_path_exists_side_effect, expected_output
):
    # Configure the side effect for `pathlib.Path.exists` for the current test case
    mock_path_exists.side_effect = mock_path_exists_side_effect

    # Create a deep copy of base arguments to avoid side effects across test runs
    current_args = args_modifier(base_args_template.copy())

    # Convert Path objects to strings as the function signature expects strings
    func_args = {k: str(v) if isinstance(v, Path) else v for k, v in current_args.items()}

    try:
        # Call the function under test
        result = calculate_irrbb_valuation(**func_args)

        # Assert for successful execution (result is None, and mocks were called)
        assert result is expected_output
        if expected_output is None:
            # For a successful run, verify that attempts were made to open output files for writing
            # (assuming internal implementation would call open for these)
            assert mock_open.called

    except Exception as e:
        # Assert that an exception was raised and its type matches the expected_output
        assert isinstance(e, expected_output)

        # Further assertions on error messages for clarity and robustness (assuming standard error messages)
        if expected_output == FileNotFoundError:
            if "cleaned_positions" in test_id:
                assert f"File not found: {func_args['cleaned_positions_path']}" in str(e)
            elif "mortgage_model" in test_id:
                assert f"File not found: {func_args['mortgage_model_path']}" in str(e)
        elif expected_output == TypeError:
            assert "baseline_yield_curve must be a yield curve object" in str(e)
        elif expected_output == ValueError:
            assert "At least one scenario yield curve must be provided" in str(e)