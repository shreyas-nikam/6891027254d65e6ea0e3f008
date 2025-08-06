import pytest
import pandas as pd
from definition_79aa796eaed24046bcd53e88b249e494 import calculate_nii

# --- Test Data Setup ---
# DataFrame with various interest income and expense entries for testing horizons.
# It includes entries beyond a 12-month horizon to test filtering.
df_standard_cashflows = pd.DataFrame({
    'month': [1, 2, 3, 6, 12, 13, 1, 2, 3, 6, 12, 13],
    'cashflow_type': ['interest_income_asset'] * 6 + ['interest_expense_liability'] * 6,
    'amount': [100, 100, 100, 100, 100, 50, 20, 20, 20, 20, 20, 10]
})
# Expected NII for 12 months:
# Income (months 1,2,3,6,12): 100*5 = 500
# Expense (months 1,2,3,6,12): 20*5 = 100
# Total for 12 months: 500 - 100 = 400.0

# Expected NII for 6 months:
# Income (months 1,2,3,6): 100*4 = 400
# Expense (months 1,2,3,6): 20*4 = 80
# Total for 6 months: 400 - 80 = 320.0

# An empty DataFrame to test edge case where no cashflows exist.
df_empty_cashflows = pd.DataFrame(columns=['month', 'cashflow_type', 'amount'])

# DataFrame where interest expense is higher than interest income, leading to negative NII.
df_negative_nii_cashflows = pd.DataFrame({
    'month': [1, 2, 3, 4, 1, 2, 3, 4],
    'cashflow_type': ['interest_income_asset'] * 4 + ['interest_expense_liability'] * 4,
    'amount': [50, 50, 50, 50, 150, 150, 150, 150]
})
# Expected NII for 3 months:
# Income (months 1,2,3): 50*3 = 150
# Expense (months 1,2,3): 150*3 = 450
# Total for 3 months: 150 - 450 = -300.0


# --- Pytest Test Cases ---
@pytest.mark.parametrize(
    "cashflows_df, horizon_months, expected",
    [
        # Test Case 1: Standard calculation - Positive NII over default 12-month horizon.
        (df_standard_cashflows, 12, 400.0),

        # Test Case 2: Custom horizon - Positive NII over a shorter, specified horizon (6 months).
        (df_standard_cashflows, 6, 320.0),

        # Test Case 3: Edge Case - Empty cashflows DataFrame.
        # Should result in 0 NII as there are no cashflows.
        (df_empty_cashflows, 12, 0.0),

        # Test Case 4: Edge Case - Horizon set to 0 months.
        # Should result in 0 NII as no months are included in the calculation.
        (df_standard_cashflows, 0, 0.0),

        # Test Case 5: Combination of edge/error cases - Negative NII and Invalid input types.
        # Sub-case 5a: Calculation resulting in negative NII.
        (df_negative_nii_cashflows, 3, -300.0),
        # Sub-case 5b: Invalid cashflows_df type (e.g., None instead of DataFrame).
        (None, 12, TypeError),
        # Sub-case 5c: Invalid horizon_months type (e.g., string instead of int).
        (df_standard_cashflows, 'invalid', TypeError),
        # Sub-case 5d: Negative horizon_months.
        (df_standard_cashflows, -5, ValueError),
    ]
)
def test_calculate_nii(cashflows_df, horizon_months, expected):
    """
    Tests the calculate_nii function for correct NII calculation under various scenarios,
    including standard operations, custom horizons, empty data, zero horizon, negative NII,
    and appropriate error handling for invalid input types or values.
    """
    try:
        # Call the function under test, assuming it's imported directly as specified.
        result = calculate_nii(cashflows_df, horizon_months)
        assert result == expected
    except Exception as e:
        # If an exception is expected, verify its type.
        assert isinstance(e, expected)