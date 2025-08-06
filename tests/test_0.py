import pytest
import os
import pandas as pd
from pathlib import Path
import tempfile

# Keep the `your_module` block as it is. DO NOT REPLACE or REMOVE the block.
from definition_a030173ade0a4ef29f96db7b669e49c3 import generate_synthetic_positions_data

# Define expected columns based on the specification
EXPECTED_COLUMNS = [
    'instrument_id', 'instrument_type', 'side', 'notional_amt', 'currency',
    'rate_type', 'fixed_rate', 'float_index', 'spread_bps', 'payment_freq',
    'maturity_date', 'next_reprice_date', 'optionality_flag',
    'core_fraction', 'prepay_rate'
]

@pytest.fixture
def temp_output_file(tmp_path):
    """Provides a temporary file path for output."""
    return tmp_path / "test_positions.csv"

def test_generate_synthetic_positions_data_happy_path(temp_output_file):
    """
    Test case 1: Ensures data generation works with valid inputs,
    creates a CSV, and contains expected columns and adheres to minimum rows.
    """
    num_rows_requested = 5
    generate_synthetic_positions_data(num_rows_requested, str(temp_output_file))

    # Assert file exists
    assert temp_output_file.exists()
    assert temp_output_file.stat().st_size > 0 # Ensure file is not empty

    # Assert file is a valid CSV and contains data
    df = pd.read_csv(temp_output_file)

    # The specification states "Ensure a minimum of 1,000 rows" in the code requirements,
    # despite the function argument `num_rows` being described as "The minimum number of rows to generate".
    # We will enforce the stricter (internal) minimum of 1000 rows as per the detailed spec.
    assert df.shape[0] >= max(num_rows_requested, 1000)

    # Assert expected columns are present
    assert all(col in df.columns for col in EXPECTED_COLUMNS)

def test_generate_synthetic_positions_data_zero_rows_requested(temp_output_file):
    """
    Test case 2: Ensures data generation works when 0 rows are requested,
    adhering to the internal minimum (e.g., 1000) as per specification.
    """
    num_rows_requested = 0
    generate_synthetic_positions_data(num_rows_requested, str(temp_output_file))

    assert temp_output_file.exists()
    assert temp_output_file.stat().st_size > 0 # Ensure file is not empty

    df = pd.read_csv(temp_output_file)

    # Even if 0 rows are requested, the spec says "Ensure a minimum of 1,000 rows."
    assert df.shape[0] >= 1000
    assert all(col in df.columns for col in EXPECTED_COLUMNS)

def test_generate_synthetic_positions_data_invalid_num_rows_type():
    """
    Test case 3: Ensures TypeError is raised for invalid num_rows type (e.g., string).
    """
    invalid_num_rows = "invalid_number"
    # Use a temporary path to avoid polluting the test directory
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "dummy.csv")
        with pytest.raises(TypeError):
            generate_synthetic_positions_data(invalid_num_rows, output_path)

def test_generate_synthetic_positions_data_invalid_output_path_type():
    """
    Test case 4: Ensures TypeError is raised for invalid output_file_path type (e.g., int).
    """
    num_rows = 10
    invalid_output_path = 123
    with pytest.raises(TypeError):
        generate_synthetic_positions_data(num_rows, invalid_output_path)

def test_generate_synthetic_positions_data_non_existent_directory(tmp_path):
    """
    Test case 5: Ensures an appropriate error is raised if the output directory does not exist.
    """
    # Create a path that includes a non-existent sub-directory
    non_existent_dir = tmp_path / "non_existent_dir_12345"
    output_file_path = non_existent_dir / "test_non_existent_dir.csv"

    num_rows = 5

    # Expect FileNotFoundError or OSError, as pandas' to_csv would typically raise this
    # if the parent directory does not exist and `makedirs` is not implicitly called.
    with pytest.raises((FileNotFoundError, OSError)):
        generate_synthetic_positions_data(num_rows, str(output_file_path))