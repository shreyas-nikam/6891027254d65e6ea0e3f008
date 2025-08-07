import pytest
import pandas as pd
import pandas.testing as tm # Import for robust DataFrame comparison

from definition_df7c6c7ff4ed4f4aa08e345810943e82 import calculate_net_gap

@pytest.mark.parametrize("input_df, expected_output", [
    # Test Case 1: Standard functionality - Mixed assets and liabilities across multiple buckets
    # Expect correct aggregation and net gap calculation for multiple buckets and categories.
    (
        pd.DataFrame({
            'Amount': [100, 200, 50, 150, 300, 250],
            'Category': ['asset', 'asset', 'liability', 'liability', 'asset', 'liability'],
            'Basel_Bucket': ['0-1M', '1-3M', '0-1M', '1-3M', '0-1M', '3-6M']
        }),
        pd.DataFrame({
            'Basel_Bucket': ['0-1M', '1-3M', '3-6M'],
            'Total_Inflows': [400, 200, 0],
            'Total_Outflows': [50, 150, 250],
            'Net_Gap': [350, 50, -250]
        }).astype({ # Ensure dtypes are consistent with what a typical groupby aggregation would yield
            'Basel_Bucket': 'object',
            'Total_Inflows': 'int64',
            'Total_Outflows': 'int64',
            'Net_Gap': 'int64'
        })
    ),
    # Test Case 2: Edge case - Empty DataFrame
    # Expect an empty DataFrame with the correct column names and dtypes.
    (
        pd.DataFrame(columns=['Amount', 'Category', 'Basel_Bucket']),
        pd.DataFrame(columns=['Basel_Bucket', 'Total_Inflows', 'Total_Outflows', 'Net_Gap']).astype({
            'Basel_Bucket': 'object',
            'Total_Inflows': 'int64',
            'Total_Outflows': 'int64',
            'Net_Gap': 'int64'
        })
    ),
    # Test Case 3: Edge case - All inflows (assets only)
    # Expect Total_Outflows to be 0 and Net_Gap equal to Total_Inflows.
    (
        pd.DataFrame({
            'Amount': [100, 200, 300],
            'Category': ['asset', 'asset', 'asset'],
            'Basel_Bucket': ['0-1M', '1-3M', '0-1M']
        }),
        pd.DataFrame({
            'Basel_Bucket': ['0-1M', '1-3M'],
            'Total_Inflows': [400, 200],
            'Total_Outflows': [0, 0],
            'Net_Gap': [400, 200]
        }).astype({
            'Basel_Bucket': 'object',
            'Total_Inflows': 'int64',
            'Total_Outflows': 'int64',
            'Net_Gap': 'int64'
        })
    ),
    # Test Case 4: Edge case - All outflows (liabilities only)
    # Expect Total_Inflows to be 0 and Net_Gap equal to negative Total_Outflows.
    (
        pd.DataFrame({
            'Amount': [100, 200, 300],
            'Category': ['liability', 'liability', 'liability'],
            'Basel_Bucket': ['0-1M', '1-3M', '0-1M']
        }),
        pd.DataFrame({
            'Basel_Bucket': ['0-1M', '1-3M'],
            'Total_Inflows': [0, 0],
            'Total_Outflows': [400, 200],
            'Net_Gap': [-400, -200]
        }).astype({
            'Basel_Bucket': 'object',
            'Total_Inflows': 'int64',
            'Total_Outflows': 'int64',
            'Net_Gap': 'int64'
        })
    ),
    # Test Case 5: Error handling - Invalid input type
    # Expect a TypeError if the input is not a pandas DataFrame.
    ("this is not a dataframe", TypeError),
])
def test_calculate_net_gap(input_df, expected_output):
    # Check if the expected_output is an Exception type
    if isinstance(expected_output, type) and issubclass(expected_output, Exception):
        with pytest.raises(expected_output):
            calculate_net_gap(input_df)
    else:
        # For valid DataFrame inputs, perform the calculation
        actual_output = calculate_net_gap(input_df)

        # Sort both actual and expected DataFrames by 'Basel_Bucket' and reset index
        # This makes the comparison robust against potential differences in row order,
        # which can occur with groupby operations.
        actual_output_sorted = actual_output.sort_values(by='Basel_Bucket').reset_index(drop=True)
        expected_output_sorted = expected_output.sort_values(by='Basel_Bucket').reset_index(drop=True)

        # Use pandas.testing.assert_frame_equal for comprehensive DataFrame comparison.
        # This checks values, column names, index, and dtypes.
        tm.assert_frame_equal(actual_output_sorted, expected_output_sorted)