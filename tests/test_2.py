import pytest
import pandas as pd
import io
import numpy as np

# Keep a placeholder definition_b1918b60bc4341ff92453be9f49b7950 for the import of the module.
# Keep the `your_module` block as it is. DO NOT REPLACE or REMOVE the block.
from definition_b1918b60bc4341ff92453be9f49b7950 import display_dataframe_info


@pytest.mark.parametrize("input, expected", [
    # Test Case 1: Standard DataFrame with multiple columns and rows
    (pd.DataFrame({'col_int': [1, 2, 3], 'col_str': ['A', 'B', 'C']}), None),

    # Test Case 2: Empty DataFrame
    (pd.DataFrame(), None),

    # Test Case 3: DataFrame with NaNs and Mixed Data Types
    (pd.DataFrame({'num_col': [10.0, 20.0, np.nan], 'str_col': ['alpha', None, 'beta'], 'bool_col': [True, False, True]}), None),

    # Test Case 4: Non-DataFrame input (should raise TypeError)
    ([1, 2, 3], TypeError),

    # Test Case 5: DataFrame with a single row and a single column
    (pd.DataFrame({'single_value': [42]}), None),
])
def test_display_dataframe_info(capsys, input, expected):
    try:
        # Call the function under test
        returned_value = display_dataframe_info(input)

        # Assert the return value for valid DataFrame cases (should always be None)
        assert returned_value is expected

        # Capture output for valid DataFrame cases
        captured = capsys.readouterr()
        output = captured.out

        # Assert that the function printed something to stdout
        assert output is not None and output != ""

        # Check for expected section headers in the output
        assert "DataFrame Head:" in output
        assert "DataFrame Info:" in output
        assert "DataFrame Description:" in output

        # Specific content checks based on the input DataFrame structure
        if input.empty:
            assert "Empty DataFrame" in output
            assert "0 entries" in output  # From df.info()
            assert "Index: []" in output # From df.describe() on an empty DF
        elif 'col_int' in input.columns: # Test Case 1 (Standard DataFrame)
            assert 'col_int' in output
            assert 'col_str' in output
            assert '3 rows' in output
            assert 'int64' in output
            assert 'object' in output
            assert 'mean' in output
        elif 'num_col' in input.columns: # Test Case 3 (NaNs and Mixed Types)
            assert 'num_col' in output
            assert 'str_col' in output
            assert 'bool_col' in output
            assert '2 non-null' in output # For num_col from df.info() (because of np.nan)
            assert 'float64' in output
            assert 'object' in output
            assert 'bool' in output
            assert 'count' in output
        elif 'single_value' in input.columns: # Test Case 5 (Single row/column)
            assert 'single_value' in output
            assert '1 row' in output
            assert 'count    1.0' in output
            assert 'mean     42.0' in output

    except Exception as e:
        # For cases where an exception is expected
        assert isinstance(e, expected)
        # Check the error message for TypeError, assuming the function provides a helpful message
        if expected is TypeError:
            assert "pandas DataFrame" in str(e)