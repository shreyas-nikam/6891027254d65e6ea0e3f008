import pytest
import pandas as pd
import numpy as np

# definition_82d838e8b45649d0bf8424c61a6826ed block - DO NOT REPLACE or REMOVE
from definition_82d838e8b45649d0bf8424c61a6826ed import IRRBBEngine
# </your_module>

# Helper function for yield curve interpolation
def get_yield_for_tenor(yield_curve_series, tenor_str):
    tenor_td = pd.to_timedelta(tenor_str)
    
    if not isinstance(yield_curve_series.index, pd.TimedeltaIndex):
        yield_curve_series.index = pd.to_timedelta(yield_curve_series.index)
    
    if tenor_td in yield_curve_series.index:
        return yield_curve_series.loc[tenor_td]
    
    sorted_index = yield_curve_series.index.sort_values()
    lower_bound_idx = sorted_index[sorted_index <= tenor_td].max()
    upper_bound_idx = sorted_index[sorted_index >= tenor_td].min()
    
    if pd.isna(lower_bound_idx) and pd.isna(upper_bound_idx):
        raise ValueError("Yield curve is empty or invalid for interpolation.")
    elif pd.isna(lower_bound_idx):
        return yield_curve_series.loc[sorted_index.min()]
    elif pd.isna(upper_bound_idx):
        return yield_curve_series.loc[sorted_index.max()]
    
    y0, y1 = yield_curve_series.loc[lower_bound_idx], yield_curve_series.loc[upper_bound_idx]
    x0, x1 = lower_bound_idx.total_seconds(), upper_bound_idx.total_seconds()
    x = tenor_td.total_seconds()
    
    if x0 == x1:
        return y0
        
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)

# Mock class to simulate `self` for the `adjust_behavioral_cashflows` method
class MockIRRBBEngineForTest:
    def __init__(self, baseline_yield_curve, assumptions_config):
        self.baseline_yield_curve = baseline_yield_curve
        self.assumptions_config = assumptions_config

@pytest.fixture
def sample_cashflows_df():
    dates = pd.date_range(start='2023-01-31', periods=12, freq='M')
    
    mortgage_cfs = pd.DataFrame({
        'instrument_id': ['MORTGAGE_001'] * 12,
        'instrument_type': ['Mortgage'] * 12,
        'cashflow_date': dates,
        'principal_cashflow': [1000.0] * 12,
        'interest_cashflow': [50.0] * 12,
        'is_behavioral_mortgage': [True] * 12,
        'is_behavioral_NMD': [False] * 12,
        'current_balance': np.linspace(90000, 80000, 12)
    })
    
    nmd_cfs = pd.DataFrame({
        'instrument_id': ['NMD_001'] * 12,
        'instrument_type': ['NMD'] * 12,
        'cashflow_date': dates,
        'principal_cashflow': [500.0] * 12,
        'interest_cashflow': [10.0] * 12,
        'is_behavioral_mortgage': [False] * 12,
        'is_behavioral_NMD': [True] * 12,
        'current_balance': np.linspace(45000, 40000, 12)
    })

    other_cfs = pd.DataFrame({
        'instrument_id': ['FIXED_BOND_001', 'FLOATING_LOAN_001'],
        'instrument_type': ['Fixed Bond', 'Floating Loan'],
        'cashflow_date': [pd.Timestamp('2023-01-31'), pd.Timestamp('2023-01-31')],
        'principal_cashflow': [2000.0, 1500.0],
        'interest_cashflow': [70.0, 60.0],
        'is_behavioral_mortgage': [False, False],
        'is_behavioral_NMD': [False, False],
        'current_balance': [0.0, 0.0]
    })
    
    return pd.concat([mortgage_cfs, nmd_cfs, other_cfs], ignore_index=True)

@pytest.fixture
def baseline_yield_curve_fixture():
    baseline_yc_data = {
        '1M': 0.01, '3M': 0.011, '6M': 0.012, '1Y': 0.015,
        '2Y': 0.018, '3Y': 0.02, '5Y': 0.022, '7Y': 0.024,
        '10Y': 0.025, '15Y': 0.026, '20Y': 0.027, '30Y': 0.028
    }
    return pd.Series(baseline_yc_data, name='yield', index=list(baseline_yc_data.keys()))

@pytest.fixture
def irrbb_engine_instance(baseline_yield_curve_fixture):
    assumptions = {
        'behavioral_rates': {
            'mortgage_prepayment': {
                'baseline_annual_rate': 0.05,
                'shock_sensitivity': {
                    'fall': 0.02,
                    'rise': -0.01
                }
            },
            'NMD_beta': 0.5,
            'NMD_principal_sensitivity': {
                'fall_threshold_bp': -50,
                'rise_threshold_bp': 50,
                'principal_adjustment_factor': 0.001
            }
        }
    }
    return MockIRRBBEngineForTest(baseline_yield_curve_fixture, assumptions)

def test_adjust_behavioral_cashflows_rates_fall(sample_cashflows_df, baseline_yield_curve_fixture, irrbb_engine_instance):
    scenario_down_yc_data = {k: v - 0.01 for k, v in baseline_yield_curve_fixture.items()}
    scenario_down_yield_curve = pd.Series(scenario_down_yc_data, name='yield', index=list(scenario_down_yc_data.keys()))

    adjusted_df = IRRBBEngine.adjust_behavioral_cashflows(irrbb_engine_instance, sample_cashflows_df.copy(), scenario_down_yield_curve)

    mortgage_cfs_adj = adjusted_df[adjusted_df['instrument_type'] == 'Mortgage']
    mortgage_cfs_orig = sample_cashflows_df[sample_cashflows_df['instrument_type'] == 'Mortgage']
    
    mortgage_baseline_rate = irrbb_engine_instance.assumptions_config['behavioral_rates']['mortgage_prepayment']['baseline_annual_rate']
    mortgage_fall_sensitivity = irrbb_engine_instance.assumptions_config['behavioral_rates']['mortgage_prepayment']['shock_sensitivity']['fall']
    effective_mortgage_rate = mortgage_baseline_rate + mortgage_fall_sensitivity
    
    for idx, row in mortgage_cfs_orig.iterrows():
        adjusted_principal = mortgage_cfs_adj[mortgage_cfs_adj['cashflow_date'] == row['cashflow_date']]['principal_cashflow'].iloc[0]
        expected_added_prepayment_monthly = (row['current_balance'] * effective_mortgage_rate) / 12
        expected_total_principal = row['principal_cashflow'] + expected_added_prepayment_monthly
        
        np.testing.assert_allclose(adjusted_principal, expected_total_principal, rtol=1e-5)
        assert adjusted_principal > row['principal_cashflow']

    nmd_cfs_adj = adjusted_df[adjusted_df['instrument_type'] == 'NMD']
    nmd_cfs_orig = sample_cashflows_df[sample_cashflows_df['instrument_type'] == 'NMD']
    
    nmd_principal_adj_factor = irrbb_engine_instance.assumptions_config['behavioral_rates']['NMD_principal_sensitivity']['principal_adjustment_factor']
    nmd_fall_threshold = irrbb_engine_instance.assumptions_config['behavioral_rates']['NMD_principal_sensitivity']['fall_threshold_bp'] / 10000
    
    baseline_1m_rate = get_yield_for_tenor(baseline_yield_curve_fixture, '1M')
    scenario_1m_rate = get_yield_for_tenor(scenario_down_yield_curve, '1M')
    rate_change_1m = scenario_1m_rate - baseline_1m_rate

    for idx, row in nmd_cfs_orig.iterrows():
        adjusted_interest = nmd_cfs_adj[nmd_cfs_adj['cashflow_date'] == row['cashflow_date']]['interest_cashflow'].iloc[0]
        adjusted_principal = nmd_cfs_adj[nmd_cfs_adj['cashflow_date'] == row['cashflow_date']]['principal_cashflow'].iloc[0]
        
        assert adjusted_interest < row['interest_cashflow']
        
        expected_principal_adjustment = 0
        if rate_change_1m < nmd_fall_threshold:
             expected_principal_adjustment = row['current_balance'] * nmd_principal_adj_factor
        
        expected_total_principal = row['principal_cashflow'] + expected_principal_adjustment
        np.testing.assert_allclose(adjusted_principal, expected_total_principal, rtol=1e-5)
        assert adjusted_principal > row['principal_cashflow']

def test_adjust_behavioral_cashflows_rates_rise(sample_cashflows_df, baseline_yield_curve_fixture, irrbb_engine_instance):
    scenario_up_yc_data = {k: v + 0.01 for k, v in baseline_yield_curve_fixture.items()}
    scenario_up_yield_curve = pd.Series(scenario_up_yc_data, name='yield', index=list(scenario_up_yc_data.keys()))

    adjusted_df = IRRBBEngine.adjust_behavioral_cashflows(irrbb_engine_instance, sample_cashflows_df.copy(), scenario_up_yield_curve)

    mortgage_cfs_adj = adjusted_df[adjusted_df['instrument_type'] == 'Mortgage']
    mortgage_cfs_orig = sample_cashflows_df[sample_cashflows_df['instrument_type'] == 'Mortgage']
    
    mortgage_baseline_rate = irrbb_engine_instance.assumptions_config['behavioral_rates']['mortgage_prepayment']['baseline_annual_rate']
    mortgage_rise_sensitivity = irrbb_engine_instance.assumptions_config['behavioral_rates']['mortgage_prepayment']['shock_sensitivity']['rise']
    effective_mortgage_rate = mortgage_baseline_rate + mortgage_rise_sensitivity
    
    for idx, row in mortgage_cfs_orig.iterrows():
        adjusted_principal = mortgage_cfs_adj[mortgage_cfs_adj['cashflow_date'] == row['cashflow_date']]['principal_cashflow'].iloc[0]
        expected_added_prepayment_monthly = (row['current_balance'] * effective_mortgage_rate) / 12
        expected_total_principal = row['principal_cashflow'] + expected_added_prepayment_monthly
        
        np.testing.assert_allclose(adjusted_principal, expected_total_principal, rtol=1e-5)
        assert adjusted_principal < row['principal_cashflow']

    nmd_cfs_adj = adjusted_df[adjusted_df['instrument_type'] == 'NMD']
    nmd_cfs_orig = sample_cashflows_df[sample_cashflows_df['instrument_type'] == 'NMD']
    
    nmd_principal_adj_factor = irrbb_engine_instance.assumptions_config['behavioral_rates']['NMD_principal_sensitivity']['principal_adjustment_factor']
    nmd_rise_threshold = irrbb_engine_instance.assumptions_config['behavioral_rates']['NMD_principal_sensitivity']['rise_threshold_bp'] / 10000
    
    baseline_1m_rate = get_yield_for_tenor(baseline_yield_curve_fixture, '1M')
    scenario_1m_rate = get_yield_for_tenor(scenario_up_yield_curve, '1M')
    rate_change_1m = scenario_1m_rate - baseline_1m_rate

    for idx, row in nmd_cfs_orig.iterrows():
        adjusted_interest = nmd_cfs_adj[nmd_cfs_adj['cashflow_date'] == row['cashflow_date']]['interest_cashflow'].iloc[0]
        adjusted_principal = nmd_cfs_adj[nmd_cfs_adj['cashflow_date'] == row['cashflow_date']]['principal_cashflow'].iloc[0]

        assert adjusted_interest > row['interest_cashflow']
        
        expected_principal_adjustment = 0
        if rate_change_1m > nmd_rise_threshold:
             expected_principal_adjustment = -row['current_balance'] * nmd_principal_adj_factor
        
        expected_total_principal = row['principal_cashflow'] + expected_principal_adjustment
        np.testing.assert_allclose(adjusted_principal, expected_total_principal, rtol=1e-5)
        assert adjusted_principal < row['principal_cashflow']

def test_adjust_behavioral_cashflows_no_behavioral_instruments(baseline_yield_curve_fixture, irrbb_engine_instance):
    non_behavioral_df = pd.DataFrame({
        'instrument_id': ['FIXED_BOND_001', 'FLOATING_LOAN_001'],
        'instrument_type': ['Fixed Bond', 'Floating Loan'],
        'cashflow_date': [pd.Timestamp('2023-01-31'), pd.Timestamp('2023-01-31')],
        'principal_cashflow': [2000.0, 1500.0],
        'interest_cashflow': [70.0, 60.0],
        'is_behavioral_mortgage': [False, False],
        'is_behavioral_NMD': [False, False],
        'current_balance': [0.0, 0.0]
    })
    
    scenario_yield_curve = pd.Series({'1M': 0.005, '10Y': 0.015}, index=['1M', '10Y'])

    adjusted_df = IRRBBEngine.adjust_behavioral_cashflows(irrbb_engine_instance, non_behavioral_df.copy(), scenario_yield_curve)
    
    pd.testing.assert_frame_equal(adjusted_df, non_behavioral_df)

def test_adjust_behavioral_cashflows_empty_df(baseline_yield_curve_fixture, irrbb_engine_instance):
    empty_df = pd.DataFrame(columns=[
        'instrument_id', 'instrument_type', 'cashflow_date', 
        'principal_cashflow', 'interest_cashflow', 
        'is_behavioral_mortgage', 'is_behavioral_NMD', 'current_balance'
    ])
    
    scenario_yield_curve = pd.Series({'1M': 0.005, '10Y': 0.015}, index=['1M', '10Y'])

    adjusted_df = IRRBBEngine.adjust_behavioral_cashflows(irrbb_engine_instance, empty_df.copy(), scenario_yield_curve)
    
    pd.testing.assert_frame_equal(adjusted_df, empty_df)

def test_adjust_behavioral_cashflows_unchanged_yield_curve(sample_cashflows_df, baseline_yield_curve_fixture, irrbb_engine_instance):
    unchanged_yield_curve = baseline_yield_curve_fixture.copy()

    adjusted_df = IRRBBEngine.adjust_behavioral_cashflows(irrbb_engine_instance, sample_cashflows_df.copy(), unchanged_yield_curve)

    mortgage_cfs_adj = adjusted_df[adjusted_df['instrument_type'] == 'Mortgage']
    mortgage_cfs_orig = sample_cashflows_df[sample_cashflows_df['instrument_type'] == 'Mortgage']
    
    mortgage_baseline_rate = irrbb_engine_instance.assumptions_config['behavioral_rates']['mortgage_prepayment']['baseline_annual_rate']
    
    for idx, row in mortgage_cfs_orig.iterrows():
        adjusted_principal = mortgage_cfs_adj[mortgage_cfs_adj['cashflow_date'] == row['cashflow_date']]['principal_cashflow'].iloc[0]
        expected_added_prepayment_monthly = (row['current_balance'] * mortgage_baseline_rate) / 12
        expected_total_principal = row['principal_cashflow'] + expected_added_prepayment_monthly
        
        np.testing.assert_allclose(adjusted_principal, expected_total_principal, rtol=1e-5)
        assert adjusted_principal > row['principal_cashflow']

    nmd_cfs_adj = adjusted_df[adjusted_df['instrument_type'] == 'NMD']
    nmd_cfs_orig = sample_cashflows_df[sample_cashflows_df['instrument_type'] == 'NMD']

    pd.testing.assert_series_equal(nmd_cfs_adj['interest_cashflow'].reset_index(drop=True), nmd_cfs_orig['interest_cashflow'].reset_index(drop=True), check_dtype=False)
    pd.testing.assert_series_equal(nmd_cfs_adj['principal_cashflow'].reset_index(drop=True), nmd_cfs_orig['principal_cashflow'].reset_index(drop=True), check_dtype=False)