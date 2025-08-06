import pytest
import os
from unittest.mock import patch
import io
import sys

# Keep this block as is
from definition_fc78a1592f58418b8f1c290b3d6e0be1 import verify_saved_artifacts

@patch('os.path.exists', return_value=True)
def test_1_all_artifacts_exist(mock_exists, capsys):
    """
    Test case: Verifies that the function correctly identifies all artifacts as 'FOUND'
    when they are present, and prints the appropriate success message.
    """
    artifact_list = [
        'irrbb_taiwan_positions.csv',
        'models/part1/irrbb_taiwan_mortgage_prepay_model.pkl',
        'another_dir/irrbb_taiwan_cashflows_long.parquet'
    ]
    base_directory = '/app/data'
    
    verify_saved_artifacts(artifact_list, base_directory)

    captured = capsys.readouterr()
    expected_output_lines = [
        f"Verifying artifacts in: {base_directory}",
        "[FOUND] irrbb_taiwan_positions.csv",
        "[FOUND] models/part1/irrbb_taiwan_mortgage_prepay_model.pkl",
        "[FOUND] another_dir/irrbb_taiwan_cashflows_long.parquet",
        "All required artifacts found."
    ]
    
    for line in expected_output_lines:
        assert line in captured.out
    
    # Verify os.path.exists was called for each expected full path
    mock_exists.assert_any_call(os.path.join(base_directory, 'irrbb_taiwan_positions.csv'))
    mock_exists.assert_any_call(os.path.join(base_directory, 'models/part1/irrbb_taiwan_mortgage_prepay_model.pkl'))
    mock_exists.assert_any_call(os.path.join(base_directory, 'another_dir/irrbb_taiwan_cashflows_long.parquet'))
    assert mock_exists.call_count == len(artifact_list)

def test_2_some_artifacts_missing(capsys):
    """
    Test case: Verifies that the function correctly identifies both 'FOUND' and 'MISSING'
    artifacts and prints the appropriate warning message.
    """
    artifact_list = [
        'irrbb_taiwan_eve_baseline.pkl',
        'irrbb_taiwan_nii_results.pkl',
        'missing_model.pkl'
    ]
    base_directory = '/app/data'

    # Configure mock_exists to return True for the first two artifacts, False for the third
    def mock_exists_side_effect(path):
        if 'irrbb_taiwan_eve_baseline.pkl' in path or 'irrbb_taiwan_nii_results.pkl' in path:
            return True
        elif 'missing_model.pkl' in path:
            return False
        return False # Default for unexpected paths

    with patch('os.path.exists', side_effect=mock_exists_side_effect) as mock_exists:
        verify_saved_artifacts(artifact_list, base_directory)

        captured = capsys.readouterr()
        expected_output_lines = [
            f"Verifying artifacts in: {base_directory}",
            "[FOUND] irrbb_taiwan_eve_baseline.pkl",
            "[FOUND] irrbb_taiwan_nii_results.pkl",
            "[MISSING] missing_model.pkl",
            "Some artifacts are missing."
        ]
        
        for line in expected_output_lines:
            assert line in captured.out
        
        # Verify os.path.exists was called for each expected full path
        mock_exists.assert_any_call(os.path.join(base_directory, 'irrbb_taiwan_eve_baseline.pkl'))
        mock_exists.assert_any_call(os.path.join(base_directory, 'irrbb_taiwan_nii_results.pkl'))
        mock_exists.assert_any_call(os.path.join(base_directory, 'missing_model.pkl'))
        assert mock_exists.call_count == len(artifact_list)

@patch('os.path.exists') # Patch os.path.exists, though it shouldn't be called
def test_3_empty_artifact_list(mock_exists, capsys):
    """
    Test case: Verifies that the function handles an empty artifact list gracefully,
    printing a message indicating no artifacts to verify and not checking for files.
    """
    artifact_list = []
    base_directory = '/some/path'
    
    verify_saved_artifacts(artifact_list, base_directory)

    captured = capsys.readouterr()
    assert f"Verifying artifacts in: {base_directory}" in captured.out
    assert "No artifacts specified for verification." in captured.out
    assert "All required artifacts found." not in captured.out # Should not be printed
    assert "Some artifacts are missing." not in captured.out # Should not be printed
    mock_exists.assert_not_called() # Crucially, os.path.exists should not be called

def test_4_invalid_artifact_list_type():
    """
    Test case: Verifies that the function raises a TypeError when 'artifact_list' is not a list.
    """
    invalid_artifact_lists = [None, "not_a_list", 123, {'a': 1}]
    base_directory = '/valid/path'
    
    for invalid_list in invalid_artifact_lists:
        with pytest.raises(TypeError, match="artifact_list must be a list"):
            verify_saved_artifacts(invalid_list, base_directory)

def test_5_invalid_base_directory_type():
    """
    Test case: Verifies that the function raises a TypeError when 'base_directory' is not a string.
    """
    artifact_list = ['file.csv']
    invalid_base_directories = [None, 123, ['list_path'], {'dir': '/path'}]
    
    for invalid_dir in invalid_base_directories:
        with pytest.raises(TypeError, match="base_directory must be a string"):
            verify_saved_artifacts(artifact_list, invalid_dir)