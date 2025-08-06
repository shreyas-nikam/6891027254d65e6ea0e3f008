import pytest
import pandas as pd
from datetime import date, timedelta
from scipy.interpolate import interp1d
import numpy as np

# definition_1d2f29e6c2d040bea1523b43882ee0bf
# Assume IRRBBEngine class is defined in definition_1d2f29e6c2d040bea1523b43882ee0bf
# For testing purposes, we define a mock version here that matches the signature and expected behavior.
class IRRBBEngine:
    def __init__(self, valuation_date_str="2023-01-01"):
        self.valuation_date = pd.to_datetime(valuation_date_str)

    def calculate_discount_factors(self, yield_curve, cashflow_dates):
        """
        Computes discount factors for a given set of cash flow dates based on the provided yield curve.
        The function interpolates discount rates from the yield curve for each cash flow date
        and then calculates the discount factors (DF_t = 1 / (1 + r_t)^t).
        
        Arguments:
            yield_curve (pandas.Series or pandas.DataFrame) - The yield curve to use for discounting.
            cashflow_dates (list or pandas.Series) - A list or Series of dates for which to calculate discount factors.
        
        Output:
            A Series of discount factors corresponding to the input cash flow dates.
        """
        if not isinstance(yield_curve, (pd.Series, pd.DataFrame)):
            raise TypeError("yield_curve must be a pandas Series or DataFrame.")
        if not isinstance(cashflow_dates, (list, pd.Series)):
            raise TypeError("cashflow_dates must be a list or pandas Series.")

        # Handle empty inputs
        if yield_curve.empty or not cashflow_dates:
            return pd.Series(dtype=float)

        # Ensure yield_curve index is datetime for consistent processing
        if not isinstance(yield_curve.index, pd.DatetimeIndex):
            try:
                yield_curve.index = pd.to_datetime(yield_curve.index)
            except Exception as e:
                raise ValueError(f"Could not convert yield_curve index to datetime: {e}")

        # Convert cashflow_dates to pandas Series of datetime
        try:
            if isinstance(cashflow_dates, list):
                # Using pd.to_datetime for better error handling and vectorized conversion
                cashflow_dates_series = pd.to_datetime(cashflow_dates)
            else: # pandas Series
                cashflow_dates_series = pd.to_datetime(cashflow_dates)
        except Exception as e:
            raise ValueError(f"Could not convert cashflow_dates to datetime: {e}")

        # Extract rates: if DataFrame, take the first column's values. If Series, take values directly.
        if isinstance(yield_curve, pd.DataFrame):
            # Assuming the first column contains the rates if DataFrame
            yc_rates = yield_curve.iloc[:, 0].values.astype(float)
        else: # pd.Series
            yc_rates = yield_curve.values.astype(float)

        # Get tenors (in days from valuation_date) from the yield curve
        yc_tenors_days = np.array([(d - self.valuation_date).days for d in yield_curve.index])
        
        # Sort tenors and rates for interpolation
        sort_idx = np.argsort(yc_tenors_days)
        yc_tenors_days_sorted = yc_tenors_days[sort_idx]
        yc_rates_sorted = yc_rates[sort_idx]
        
        # Create interpolation function
        # Using bounds_error=False and fill_value to clamp rates at the first/last point.
        # This is standard practice in finance for yield curve extrapolation (flat extrapolation).
        interpolator = interp1d(yc_tenors_days_sorted, yc_rates_sorted, kind='linear', 
                                  bounds_error=False, fill_value=(yc_rates_sorted[0], yc_rates_sorted[-1]))

        discount_factors = []
        original_index = cashflow_dates_series.index # Preserve original index for the output Series

        for cf_date in cashflow_dates_series:
            t_days = (cf_date - self.valuation_date).days
            
            if t_days < 0:
                raise ValueError(f"Cash flow date '{cf_date.strftime('%Y-%m-%d')}' cannot be before the valuation date '{self.valuation_date.strftime('%Y-%m-%d')}' for discount factor calculation.")
            
            # Get interpolated rate, .item() gets scalar from numpy array
            r_t = interpolator(t_days).item() 
            
            # Convert t_days to years for the formula (using 365.25 for average days in a year)
            t_years = t_days / 365.25 
            
            if (1 + r_t) <= 0:
                raise ValueError(f"Calculated rate {r_t} leads to (1+r_t) <= 0, which is invalid for discount factor calculation, especially for fractional t.")
            
            # Calculate discount factor
            df_t = 1 / ((1 + r_t)**t_years)
            discount_factors.append(df_t)
        
        return pd.Series(discount_factors, index=original_index)

# /definition_1d2f29e6c2d040bea1523b43882ee0bf # DO NOT REPLACE or REMOVE this block

# Initialize the IRRBBEngine with a fixed valuation date for consistent testing
ENGINE = IRRBBEngine(valuation_date_str="2023-01-01")

@pytest.mark.parametrize("yield_curve_data, cashflow_dates_data, expected_dfs, expected_exception", [
    # Test Case 1: Happy Path - Standard Calculation & Interpolation
    (
        pd.Series(data=[0.01, 0.02, 0.03], index=pd.to_datetime(['2023-01-01', '2024-01-01', '2025-01-01'])),
        [pd.to_datetime('2023-07-01'), pd.to_datetime('2024-01-01')],
        [1 / ((1 + 0.015)**(182.625/365.25)), 1 / ((1 + 0.02)**(365.25/365.25))],
        None
    ),
    # Test Case 2: Edge Case - Empty Cashflow Dates
    (
        pd.Series(data=[0.01, 0.02], index=pd.to_datetime(['2023-01-01', '2024-01-01'])),
        [],
        [], # Expected empty Series
        None
    ),
    # Test Case 3: Edge Case - Extrapolation (before and after curve range)
    # Valuation: 2023-01-01
    # YC: 2024-01-01 (1yr, rate 0.02), 2025-01-01 (2yr, rate 0.03)
    # CF1: 2023-07-01 (0.5yr) -> Uses first YC rate (0.02)
    # CF2: 2026-01-01 (3yr) -> Uses last YC rate (0.03)
    (
        pd.Series(data=[0.02, 0.03], index=pd.to_datetime(['2024-01-01', '2025-01-01'])),
        [pd.to_datetime('2023-07-01'), pd.to_datetime('2026-01-01')],
        [1 / ((1 + 0.02)**(182.625/365.25)), 1 / ((1 + 0.03)**(1095.75/365.25))], # 1095.75 days for 3 years
        None
    ),
    # Test Case 4: Edge Case - Zero/Negative but Valid Rates
    # Valuation: 2023-01-01
    # YC: 2023-01-01 (0yr, rate 0.00), 2023-07-01 (0.5yr, rate -0.005), 2024-01-01 (1yr, rate 0.01)
    # CF1: 2023-01-01 (0yr) -> Rate 0.00
    # CF2: 2023-04-01 (approx 0.25yr) -> Rate interpolates between 0.00 and -0.005. (90/182.625)*(-0.005) = -0.002464
    # CF3: 2024-01-01 (1yr) -> Rate 0.01
    (
        pd.Series(data=[0.00, -0.005, 0.01], index=pd.to_datetime(['2023-01-01', '2023-07-01', '2024-01-01'])),
        [pd.to_datetime('2023-01-01'), pd.to_datetime('2023-04-01'), pd.to_datetime('2024-01-01')],
        [1 / ((1 + 0.00)**0.0), 1 / ((1 + (-0.002464))**(90/365.25)), 1 / ((1 + 0.01)**1.0)],
        None
    ),
    # Test Case 5: Error Handling - Invalid Inputs (Non-date strings, Dates before valuation)
    (
        pd.Series(data=[0.01, 0.02], index=pd.to_datetime(['2023-01-01', '2024-01-01'])),
        ['invalid_date', pd.to_datetime('2022-12-01')], # First item is non-date, second is before valuation_date
        None,
        ValueError # pd.to_datetime for 'invalid_date' will raise ValueError first
    ),
])
def test_calculate_discount_factors(yield_curve_data, cashflow_dates_data, expected_dfs, expected_exception):
    if expected_exception:
        with pytest.raises(expected_exception):
            ENGINE.calculate_discount_factors(yield_curve_data, cashflow_dates_data)
    else:
        result = ENGINE.calculate_discount_factors(yield_curve_data, cashflow_dates_data)
        if len(expected_dfs) == 0:
            assert result.empty
            assert result.dtype == float
        else:
            # Using np.isclose for floating-point comparison
            assert all(np.isclose(result.values, np.array(expected_dfs), rtol=1e-5, atol=1e-8))