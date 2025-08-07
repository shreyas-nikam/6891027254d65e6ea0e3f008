import pytest
import pandas as pd
from definition_1eda19749e9b40d293fe9c1ab13641bc import generate_synthetic_portfolio

@pytest.mark.parametrize(
    "num_instruments, tier1_capital, start_date, end_date, expected_outcome",
    [
        # Test Case 1: Happy path - standard valid inputs
        (5, 1000.0, "2023-01-01", "2025-12-31", "dataframe_5_rows"),
        # Test Case 2: Edge case - zero instruments, should return an empty DataFrame
        (0, 500.0, "2023-01-01", "2024-12-31", "dataframe_0_rows"),
        # Test Case 3: Invalid input - negative number of instruments, should raise ValueError
        (-1, 1500.0, "2023-01-01", "2025-12-31", ValueError),
        # Test Case 4: Invalid date order - start_date after end_date, should raise ValueError
        (10, 2000.0, "2025-01-01", "2023-01-01", ValueError),
        # Test Case 5: Invalid type - non-float tier1_capital, should raise TypeError
        (5, "invalid_capital", "2023-01-01", "2025-12-31", TypeError),
    ]
)
def test_generate_synthetic_portfolio(num_instruments, tier1_capital, start_date, end_date, expected_outcome):
    """
    Tests the generate_synthetic_portfolio function for various valid and invalid inputs.
    """
    if isinstance(expected_outcome, type) and issubclass(expected_outcome, Exception):
        # If an exception is expected, assert that the function raises it
        with pytest.raises(expected_outcome):
            generate_synthetic_portfolio(num_instruments, tier1_capital, start_date, end_date)
    else:
        # If a DataFrame is expected, call the function and assert its properties
        df = generate_synthetic_portfolio(num_instruments, tier1_capital, start_date, end_date)

        # Assert that the returned object is a pandas DataFrame
        assert isinstance(df, pd.DataFrame)

        if expected_outcome == "dataframe_5_rows":
            # Assert that the DataFrame has the expected number of rows
            assert len(df) == 5
            # Further checks for expected columns (based on specification) could be added here
            # e.g., assert 'instrument_id' in df.columns and 'balance' in df.columns

        elif expected_outcome == "dataframe_0_rows":
            # Assert that the DataFrame is empty for num_instruments=0
            assert len(df) == 0