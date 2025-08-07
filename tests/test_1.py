import pytest
import pandas as pd
from datetime import datetime
import numpy as np

# Placeholder for your module import
from definition_6db3ba6ef96d46ababae97129f33e6bc import create_baseline_discount_curve

@pytest.mark.parametrize(
    "valuation_date, market_rates, tenors_in_months, liquidity_spread_bps, expected",
    [
        # Test Case 1: Basic valid inputs with interpolation and spread
        (
            datetime(2023, 1, 1),
            {'1M': 0.01, '1Y': 0.015, '5Y': 0.02}, # Market rates for 1 month, 12 months, 60 months
            [1, 3, 6, 12, 24, 60], # Target tenors in months, requiring interpolation
            10, # 10 bps liquidity spread
            pd.DataFrame({
                'Tenor_Months': [1, 3, 6, 12, 24, 60],
                'Discount_Rate': [
                    0.01 + 0.0010, # 1M (actual rate + spread)
                    0.010909090909090908 + 0.0010, # 3M (interpolated rate + spread)
                    0.012272727272727272 + 0.0010, # 6M (interpolated rate + spread)
                    0.015 + 0.0010, # 12M (actual rate + spread)
                    0.01625 + 0.0010, # 24M (interpolated rate + spread)
                    0.02 + 0.0010 # 60M (actual rate + spread)
                ]
            })
        ),
        # Test Case 2: Edge case - Empty market_rates dictionary
        # Should raise an error as interpolation requires data points.
        (
            datetime(2023, 1, 1),
            {},
            [1, 3, 6, 12],
            10,
            ValueError # Expected exception for insufficient data for interpolation
        ),
        # Test Case 3: Edge case - Empty tenors_in_months list
        # Should return an empty DataFrame with the correct columns, as no curve points are requested.
        (
            datetime(2023, 1, 1),
            {'1M': 0.01, '1Y': 0.015},
            [],
            10,
            pd.DataFrame(columns=['Tenor_Months', 'Discount_Rate'])
        ),
        # Test Case 4: Edge case - Single market rate point
        # A single market rate point is insufficient to construct a curve requiring interpolation,
        # typically leading to an error in interpolation libraries for standard interpolation kinds.
        (
            datetime(2023, 1, 1),
            {'1Y': 0.015}, # Only one market rate point
            [1, 3, 6, 12, 24], # Multiple target tenors
            10,
            ValueError # Expected exception (e.g., from scipy.interpolate.interp1d requiring >1 point)
        ),
        # Test Case 5: Error handling - Invalid type for liquidity_spread_bps
        # Expect a TypeError if a non-numeric value is passed for a numerical argument.
        (
            datetime(2023, 1, 1),
            {'1M': 0.01, '1Y': 0.015},
            [1, 3, 6, 12],
            "invalid_spread", # Invalid type (string instead of float)
            TypeError # Expected exception
        ),
    ]
)
def test_create_baseline_discount_curve(valuation_date, market_rates, tenors_in_months, liquidity_spread_bps, expected):
    try:
        result_df = create_baseline_discount_curve(valuation_date, market_rates, tenors_in_months, liquidity_spread_bps)
        # Assertions for successful execution (DataFrame output)
        pd.testing.assert_frame_equal(result_df, expected, check_exact=False, atol=1e-7)
    except Exception as e:
        # Assertions for expected exceptions
        assert isinstance(e, expected)