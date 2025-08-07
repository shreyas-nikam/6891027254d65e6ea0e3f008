import pytest
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from scipy.interpolate import interp1d

# definition_23bd81cc0abb43868f98f53b103b788f block
from definition_23bd81cc0abb43868f98f53b103b788f import calculate_present_value_for_cashflows
# end definition_23bd81cc0abb43868f98f53b103b788f block

# Helper function to mock the interpolation and PV calculation for expected values
# This helps ensure the test's expected values are derived consistently with the problem's logic
def _calculate_single_pv_mock(amount, cf_date, valuation_date, discount_curve_df):
    """
    Mock PV calculation logic mirroring the expected behavior of the function under test.
    Assumes linear interpolation with extrapolation for discount rates.
    """
    time_delta_days = (cf_date - valuation_date).days

    # According to EVE concept in spec, past cash flows are not part of future PV calculation.
    if time_delta_days < 0:
        return 0.0

    time_years = time_delta_days / 365.25

    if time_years == 0:
        return amount # Cash flow on valuation_date has PV equal to its amount

    # Sort discount curve for interpolation
    discount_curve_df = discount_curve_df.sort_values(by='Tenor_Months')
    tenors_years = discount_curve_df['Tenor_Months'] / 12.0
    discount_rates = discount_curve_df['Discount_Rate']

    # Create interpolation function with extrapolation
    interp_func = interp1d(tenors_years, discount_rates, kind='linear', fill_value="extrapolate")

    discount_rate = interp_func(time_years).item()

    # Simple check for very unrealistic rates that might lead to mathematical issues
    if (1 + discount_rate) <= 0:
        # This is a defensive check, unlikely for typical discount rates in finance
        raise ValueError("Discount rate leads to non-positive (1 + r)")

    pv = amount / ((1 + discount_rate)**time_years)
    return pv


# Test Case 1: Standard Scenario - Mixed Assets & Liabilities with various tenors
def test_calculate_pv_standard_mixed_cashflows():
    valuation_date = datetime(2023, 1, 1)
    cashflow_df = pd.DataFrame([
        {'Date': datetime(2024, 1, 1), 'Amount': 1000.0, 'Category': 'Asset'},     # 1 year out
        {'Date': datetime(2025, 7, 1), 'Amount': -500.0, 'Category': 'Liability'}, # 2.5 years out (interpolation)
        {'Date': datetime(2023, 7, 1), 'Amount': 200.0, 'Category': 'Asset'},      # 0.5 year out
    ])
    discount_curve = pd.DataFrame([
        {'Tenor_Months': 6, 'Discount_Rate': 0.010},
        {'Tenor_Months': 12, 'Discount_Rate': 0.020},
        {'Tenor_Months': 24, 'Discount_Rate': 0.030},
        {'Tenor_Months': 36, 'Discount_Rate': 0.035},
    ])

    # Calculate expected values using the mock helper
    expected_pv_asset1 = _calculate_single_pv_mock(1000.0, datetime(2024, 1, 1), valuation_date, discount_curve)
    expected_pv_liability1 = _calculate_single_pv_mock(-500.0, datetime(2025, 7, 1), valuation_date, discount_curve)
    expected_pv_asset2 = _calculate_single_pv_mock(200.0, datetime(2023, 7, 1), valuation_date, discount_curve)

    expected_total_pv_assets = expected_pv_asset1 + expected_pv_asset2
    expected_total_pv_liabilities = expected_pv_liability1

    total_pv_assets, total_pv_liabilities = calculate_present_value_for_cashflows(cashflow_df, discount_curve, valuation_date)

    assert abs(total_pv_assets - expected_total_pv_assets) < 1e-6
    assert abs(total_pv_liabilities - expected_total_pv_liabilities) < 1e-6


# Test Case 2: Edge Case - Empty cashflow_df and only one type of cashflow
def test_calculate_pv_empty_and_single_type_cashflows():
    valuation_date = datetime(2023, 1, 1)
    discount_curve = pd.DataFrame([
        {'Tenor_Months': 6, 'Discount_Rate': 0.01},
        {'Tenor_Months': 12, 'Discount_Rate': 0.02},
    ])

    # Test 2a: Empty cashflow_df
    empty_cashflow_df = pd.DataFrame(columns=['Date', 'Amount', 'Category'])
    total_pv_assets, total_pv_liabilities = calculate_present_value_for_cashflows(empty_cashflow_df, discount_curve, valuation_date)
    assert total_pv_assets == 0.0
    assert total_pv_liabilities == 0.0

    # Test 2b: Only assets
    assets_only_df = pd.DataFrame([
        {'Date': datetime(2024, 1, 1), 'Amount': 1000.0, 'Category': 'Asset'},
    ])
    expected_pv_asset = _calculate_single_pv_mock(1000.0, datetime(2024, 1, 1), valuation_date, discount_curve)
    total_pv_assets, total_pv_liabilities = calculate_present_value_for_cashflows(assets_only_df, discount_curve, valuation_date)
    assert abs(total_pv_assets - expected_pv_asset) < 1e-6
    assert total_pv_liabilities == 0.0

    # Test 2c: Only liabilities
    liabilities_only_df = pd.DataFrame([
        {'Date': datetime(2024, 1, 1), 'Amount': -500.0, 'Category': 'Liability'},
    ])
    expected_pv_liability = _calculate_single_pv_mock(-500.0, datetime(2024, 1, 1), valuation_date, discount_curve)
    total_pv_assets, total_pv_liabilities = calculate_present_value_for_cashflows(liabilities_only_df, discount_curve, valuation_date)
    assert total_pv_assets == 0.0
    assert abs(total_pv_liabilities - expected_pv_liability) < 1e-6


# Test Case 3: Edge Case - Cash flows on valuation_date or in the past
def test_calculate_pv_on_or_past_valuation_date():
    valuation_date = datetime(2023, 6, 15)
    cashflow_df = pd.DataFrame([
        {'Date': datetime(2023, 6, 15), 'Amount': 500.0, 'Category': 'Asset'},      # On valuation date
        {'Date': datetime(2023, 6, 16), 'Amount': -100.0, 'Category': 'Liability'}, # 1 day after (very short tenor)
        {'Date': datetime(2023, 5, 15), 'Amount': 200.0, 'Category': 'Asset'},      # Past cash flow
    ])
    discount_curve = pd.DataFrame([
        {'Tenor_Months': 1, 'Discount_Rate': 0.005},
        {'Tenor_Months': 6, 'Discount_Rate': 0.010},
    ])

    expected_pv_asset_on_date = _calculate_single_pv_mock(500.0, datetime(2023, 6, 15), valuation_date, discount_curve)
    expected_pv_liability_1_day = _calculate_single_pv_mock(-100.0, datetime(2023, 6, 16), valuation_date, discount_curve)
    expected_pv_asset_past = _calculate_single_pv_mock(200.0, datetime(2023, 5, 15), valuation_date, discount_curve) # Should be 0.0

    expected_total_pv_assets = expected_pv_asset_on_date + expected_pv_asset_past
    expected_total_pv_liabilities = expected_pv_liability_1_day

    total_pv_assets, total_pv_liabilities = calculate_present_value_for_cashflows(cashflow_df, discount_curve, valuation_date)

    assert abs(total_pv_assets - expected_total_pv_assets) < 1e-6
    assert abs(total_pv_liabilities - expected_total_pv_liabilities) < 1e-6


# Test Case 4: Discount curve behavior - interpolation and extrapolation
def test_calculate_pv_discount_curve_interpolation_extrapolation():
    valuation_date = datetime(2023, 1, 1)
    cashflow_df = pd.DataFrame([
        {'Date': datetime(2024, 7, 1), 'Amount': 1000.0, 'Category': 'Asset'}, # 1.5 years out (interpolation)
        {'Date': datetime(2030, 1, 1), 'Amount': -2000.0, 'Category': 'Liability'}, # 7 years out (extrapolation beyond max tenor)
        {'Date': datetime(2022, 12, 1), 'Amount': 500.0, 'Category': 'Asset'} # Past (ignored)
    ])
    discount_curve = pd.DataFrame([
        {'Tenor_Months': 12, 'Discount_Rate': 0.020}, # 1 year
        {'Tenor_Months': 24, 'Discount_Rate': 0.030}, # 2 years
        {'Tenor_Months': 60, 'Discount_Rate': 0.040}, # 5 years
    ])

    expected_pv_asset_interp = _calculate_single_pv_mock(1000.0, datetime(2024, 7, 1), valuation_date, discount_curve)
    expected_pv_liability_extrap = _calculate_single_pv_mock(-2000.0, datetime(2030, 1, 1), valuation_date, discount_curve)
    expected_pv_asset_past = _calculate_single_pv_mock(500.0, datetime(2022, 12, 1), valuation_date, discount_curve) # Should be 0.0

    expected_total_pv_assets = expected_pv_asset_interp + expected_pv_asset_past
    expected_total_pv_liabilities = expected_pv_liability_extrap

    total_pv_assets, total_pv_liabilities = calculate_present_value_for_cashflows(cashflow_df, discount_curve, valuation_date)

    assert abs(total_pv_assets - expected_total_pv_assets) < 1e-6
    assert abs(total_pv_liabilities - expected_total_pv_liabilities) < 1e-6


# Test Case 5: Error Handling for Invalid Inputs
@pytest.mark.parametrize("cashflow_df_input, discount_curve_input, valuation_date_input, expected_exception", [
    (None, pd.DataFrame(), datetime.now(), TypeError), # cashflow_df is not DataFrame
    (pd.DataFrame(), None, datetime.now(), TypeError), # discount_curve is not DataFrame
    (pd.DataFrame([{'Date': datetime.now(), 'Amount': 100.0, 'Category': 'Asset'}]), 
     pd.DataFrame([{'Tenor_Months': 12, 'Discount_Rate': 0.02}]), # Only one point in discount curve
     datetime.now(), ValueError), 
    (pd.DataFrame(), pd.DataFrame([{'Tenor_Months': 12, 'Discount_Rate': 0.02}, {'Tenor_Months': 24, 'Discount_Rate': 0.03}]), 
     "2023-01-01", TypeError), # valuation_date is not datetime
    (pd.DataFrame([{'Date': datetime.now(), 'Value': 100, 'Type': 'Asset'}]), # Missing 'Amount', 'Category'
     pd.DataFrame([{'Tenor_Months': 12, 'Discount_Rate': 0.02}, {'Tenor_Months': 24, 'Discount_Rate': 0.03}]), 
     datetime.now(), ValueError),
    (pd.DataFrame([{'Date': datetime.now(), 'Amount': 100.0, 'Category': 'Asset'}]), 
     pd.DataFrame([{'Tenor': 12, 'Rate': 0.02}, {'Tenor': 24, 'Rate': 0.03}]), # Missing 'Tenor_Months', 'Discount_Rate'
     datetime.now(), ValueError),
    (pd.DataFrame([{'Date': datetime.now(), 'Amount': 100.0, 'Category': 'Unknown'}]), # Invalid 'Category'
     pd.DataFrame([{'Tenor_Months': 12, 'Discount_Rate': 0.02}, {'Tenor_Months': 24, 'Discount_Rate': 0.03}]), 
     datetime.now(), ValueError),
])
def test_calculate_pv_error_handling(cashflow_df_input, discount_curve_input, valuation_date_input, expected_exception):
    with pytest.raises(expected_exception):
        calculate_present_value_for_cashflows(cashflow_df_input, discount_curve_input, valuation_date_input)