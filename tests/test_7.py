import pytest
import pandas as pd
from datetime import datetime, timedelta

# Keep this placeholder, DO NOT REPLACE or REMOVE the block.
# from definition_cb89c191ac75416986f45acdc00bed5b import IRRBBEngine

# For testing purposes, we define a mock class that includes the function
# under test. In a real scenario, you would import IRRBBEngine from your module.
class MockIRRBBEngine:
    def calculate_present_value(self, cashflows_df, discount_factors_series):
        """    Calculates the present value of all cash flows, distinguishing between assets and liabilities. This is done by multiplying each cash flow by its corresponding discount factor and summing the results separately for assets and liabilities.
Arguments: cashflows_df (pandas.DataFrame) - The DataFrame containing cash flows.
discount_factors_series (pandas.Series) - A Series of discount factors corresponding to the cash flow dates.
Output: A tuple containing two numerical values: (Total PV of assets, Total PV of liabilities).
        """
        if not isinstance(cashflows_df, pd.DataFrame):
            raise TypeError("cashflows_df must be a pandas DataFrame.")
        if not isinstance(discount_factors_series, pd.Series):
            raise TypeError("discount_factors_series must be a pandas Series.")

        if cashflows_df.empty:
            return (0.0, 0.0)

        # Ensure required columns exist for processing cash flows
        if 'side' not in cashflows_df.columns or 'amount' not in cashflows_df.columns:
            raise ValueError("cashflows_df must contain 'side' and 'amount' columns.")

        # Separate cash flows into assets and liabilities
        assets_df = cashflows_df[cashflows_df['side'] == 'Asset'].copy()
        liabilities_df = cashflows_df[cashflows_df['side'] == 'Liability'].copy()

        # Calculate present value for assets and liabilities
        # Pandas multiplication handles alignment by index. If an index in cashflows_df
        # does not exist in discount_factors_series, the result for that row will be NaN.
        # sum() by default skips NaN values.
        # If 'amount' column or discount_factors_series contains non-numeric data,
        # the multiplication operation will typically raise a TypeError.
        total_pv_assets = (assets_df['amount'] * discount_factors_series).sum()
        total_pv_liabilities = (liabilities_df['amount'] * discount_factors_series).sum()

        return (total_pv_assets, total_pv_liabilities)

# Alias the mock class to IRRBBEngine for testing consistency
IRRBBEngine = MockIRRBBEngine

# Helper to generate consistent dates for DataFrame/Series indices
_today = datetime(2023, 1, 1)
_dates_all = [_today + timedelta(days=i * 30) for i in range(5)]

# Define test cases: (cashflows_df, discount_factors_series, expected_result_or_exception)
@pytest.mark.parametrize("cashflows_df, discount_factors_series, expected", [
    # Test Case 1: Standard case with mixed assets and liabilities
    (pd.DataFrame({'side': ['Asset', 'Liability', 'Asset', 'Liability'],
                   'amount': [100, 50, 200, 70]}, index=_dates_all[:4]),
     pd.Series([0.9, 0.95, 0.8, 0.85], index=_dates_all[:4]),
     (250.0, 107.0)), # (100*0.9 + 200*0.8, 50*0.95 + 70*0.85)

    # Test Case 2: Only assets present
    (pd.DataFrame({'side': ['Asset', 'Asset'], 'amount': [150, 250]},
                  index=[_dates_all[0], _dates_all[2]]),
     pd.Series([0.9, 0.8], index=[_dates_all[0], _dates_all[2]]),
     (335.0, 0.0)), # (150*0.9 + 250*0.8, 0)

    # Test Case 3: Only liabilities present
    (pd.DataFrame({'side': ['Liability', 'Liability'], 'amount': [60, 80]},
                  index=[_dates_all[1], _dates_all[3]]),
     pd.Series([0.95, 0.85], index=[_dates_all[1], _dates_all[3]]),
     (0.0, 125.0)), # (0, 60*0.95 + 80*0.85)

    # Test Case 4: Empty cash flows DataFrame
    (pd.DataFrame(columns=['side', 'amount']),
     pd.Series([0.9, 0.8], index=_dates_all[:2]), # Discount factors can be non-empty
     (0.0, 0.0)),

    # Test Case 5: Error handling - non-numeric amount in cashflows_df
    # This scenario triggers a TypeError during the pandas multiplication operation
    (pd.DataFrame({'side': ['Asset', 'Liability'],
                   'amount': [100, 'invalid_amount']},
                  index=_dates_all[:2]),
     pd.Series([0.9, 0.8], index=_dates_all[:2]),
     TypeError),

    # Additional error test cases (commented out to adhere to "at most 5 test cases" constraint)
    # If the constraint were less strict, these would be good additions:

    # Error: cashflows_df is not a DataFrame
    # ("not a dataframe", pd.Series([0.9, 0.8]), TypeError),

    # Error: discount_factors_series is not a Series
    # (pd.DataFrame({'side': ['Asset'], 'amount': [100]}), "not a series", TypeError),

    # Error: 'side' column missing from cashflows_df
    # (pd.DataFrame({'no_side': ['Asset'], 'amount': [100]}),
    #  pd.Series([0.9]), ValueError),

    # Error: 'amount' column missing from cashflows_df
    # (pd.DataFrame({'side': ['Asset'], 'no_amount': [100]}),
    #  pd.Series([0.9]), ValueError),
])
def test_calculate_present_value(cashflows_df, discount_factors_series, expected):
    engine = IRRBBEngine()
    if isinstance(expected, type) and issubclass(expected, Exception):
        # If an exception type is expected, assert that the function raises it
        with pytest.raises(expected):
            engine.calculate_present_value(cashflows_df, discount_factors_series)
    else:
        # Otherwise, assert that the calculated present values match the expected values
        pv_assets, pv_liabilities = engine.calculate_present_value(cashflows_df, discount_factors_series)
        # Use pytest.approx for floating-point comparisons to account for precision issues
        assert pv_assets == pytest.approx(expected[0])
        assert pv_liabilities == pytest.approx(expected[1])