import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from scipy.interpolate import interp1d
import uuid
import random

# Import global constants from the main app.py file
from app import valuation_date, standard_tenors_months, market_rates_data, basel_bucket_definitions_list, shock_scenarios

@st.cache_data(show_spinner="Generating synthetic portfolio...")
def generate_synthetic_portfolio(num_instruments, tier1_capital, start_date, end_date):
    """
    Generates a synthetic banking book portfolio.
    """
    data = []

    instrument_categories = ['Loan', 'Deposit', 'Bond']
    rate_types = ['Fixed', 'Floating']
    currencies = ['TWD']
    payment_frequencies = ['Monthly', 'Quarterly', 'Semi-Annually', 'Annually']
    embedded_options = [None, 'Call', 'Put']
    indexes = ['TAIBOR 1M', 'TAIBOR 3M', 'TAIBOR 6M', None]
    
    end_date_dt = datetime.combine(end_date, datetime.min.time())
    start_date_dt = datetime.combine(start_date, datetime.min.time())

    for _ in range(num_instruments):
        instrument_id = str(uuid.uuid4())
        category = random.choice(instrument_categories)
        
        if category == 'Loan':
            balance = random.uniform(1_000_000, 100_000_000)
            is_core_NMD = False
            behavioral_flag = None
            rate_type = random.choices(['Fixed', 'Floating'], weights=[0.6, 0.4], k=1)[0] # More fixed loans
        elif category == 'Deposit':
            balance = random.uniform(500_000, 50_000_000)
            is_core_NMD = random.choices([True, False], weights=[0.3, 0.7], k=1)[0] # 30% core NMD
            behavioral_flag = 'NMD' if is_core_NMD else None
            rate_type = random.choices(['Fixed', 'Floating'], weights=[0.2, 0.8], k=1)[0] # More floating deposits
        else: # Bond
            balance = random.uniform(5_000_000, 200_000_000)
            is_core_NMD = False
            behavioral_flag = None
            rate_type = random.choices(['Fixed', 'Floating'], weights=[0.8, 0.2], k=1)[0] # More fixed bonds
        
        index = random.choice(indexes) if rate_type == 'Floating' else None
        spread_bps = random.randint(5, 50) if rate_type == 'Floating' else 0
        current_rate = random.uniform(0.01, 0.05)
        
        maturity_date = start_date_dt + relativedelta(months=random.randint(1, 360))
        if maturity_date > end_date_dt:
            maturity_date = end_date_dt

        next_repricing_date = None
        if rate_type == 'Floating':
            reprice_interval_months = random.choice([1, 3, 6, 12]) # Common repricing frequencies
            next_repricing_candidate = start_date_dt + relativedelta(months=random.randint(0, reprice_interval_months-1)) # Can be current month
            
            if next_repricing_candidate < valuation_date:
                while next_repricing_candidate < valuation_date:
                    next_repricing_candidate += relativedelta(months=reprice_interval_months)
            
            if next_repricing_candidate <= maturity_date:
                next_repricing_date = next_repricing_candidate


        payment_freq = random.choice(payment_frequencies)
        currency = random.choice(currencies)
        embedded_option = random.choice(embedded_options) if random.random() < 0.1 else None # 10% chance of option

        data.append({
            'instrument_id': instrument_id,
            'category': category,
            'balance': balance,
            'rate_type': rate_type,
            'index': index,
            'spread_bps': spread_bps,
            'current_rate': current_rate,
            'payment_freq': payment_freq,
            'maturity_date': maturity_date,
            'next_repricing_date': next_repricing_date,
            'currency': currency,
            'embedded_option': embedded_option,
            'is_core_NMD': is_core_NMD,
            'behavioral_flag': behavioral_flag
        })
    
    df = pd.DataFrame(data)

    for col in ['maturity_date', 'next_repricing_date']:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: pd.to_datetime(x) if x is not None else None)

    final_columns = [
        'instrument_id', 'category', 'balance', 'rate_type', 'index', 'spread_bps',
        'current_rate', 'payment_freq', 'maturity_date', 'next_repricing_date',
        'currency', 'embedded_option', 'is_core_NMD', 'behavioral_flag'
    ]
    df = df.reindex(columns=final_columns)

    return df

@st.cache_data(show_spinner="Creating baseline discount curve...")
def create_baseline_discount_curve(valuation_date_param, market_rates, tenors_in_months, liquidity_spread_bps):
    """
    Creates a baseline discount curve by interpolating market rates and adding a liquidity spread.
    """
    liquidity_spread_decimal = liquidity_spread_bps / 10000.0
    
    def _parse_tenor_to_months(tenor_str):
        if tenor_str.endswith('M'):
            return int(tenor_str[:-1])
        elif tenor_str.endswith('Y'):
            return int(tenor_str[:-1]) * 12
        else:
            raise ValueError(f"Invalid tenor string format: {tenor_str}. Expected 'XM' or 'XY'.")

    parsed_market_data = []
    for tenor_str, rate in market_rates.items():
        parsed_market_data.append((_parse_tenor_to_months(tenor_str), rate))
    parsed_market_data.sort(key=lambda x: x[0])

    market_tenors_months = [item[0] for item in parsed_market_data]
    market_rates_values = [item[1] for item in parsed_market_data]

    interp_func = interp1d(market_tenors_months, market_rates_values, kind='linear', fill_value='extrapolate')
    
    interpolated_rates = interp_func(tenors_in_months)
    final_rates = interpolated_rates + liquidity_spread_decimal
    
    result_df = pd.DataFrame({
        'Tenor_Months': tenors_in_months,
        'Discount_Rate': final_rates
    })
    return result_df

def calculate_cashflows_for_instrument(instrument_data, discount_curve_df, valuation_date_param):
    """
    Calculates projected cash flows for a single instrument.
    Assumes discount_curve_df has 'date' and 'rate' columns.
    """
    cash_flows = []
    instrument_id = instrument_data['instrument_id']
    category = instrument_data['category']
    balance = instrument_data['balance']
    rate_type = instrument_data['rate_type']
    current_rate = instrument_data['current_rate']
    payment_freq = instrument_data['payment_freq']
    maturity_date = instrument_data['maturity_date']
    next_repricing_date = instrument_data['next_repricing_date']
    spread_bps = instrument_data['spread_bps']

    if pd.isna(maturity_date):
        maturity_date = valuation_date_param + relativedelta(years=100)

    if instrument_data['is_core_NMD']:
        return pd.DataFrame([])

    freq_map = {'Monthly': 1, 'Quarterly': 3, 'Semi-Annually': 6, 'Annually': 12}
    payment_interval_months = freq_map.get(payment_freq, 0)

    payment_dates = []
    temp_date = valuation_date_param
    while temp_date <= maturity_date:
        if payment_interval_months > 0:
            if (temp_date.year * 12 + temp_date.month - (valuation_date_param.year * 12 + valuation_date_param.month)) % payment_interval_months == 0:
                 if temp_date > valuation_date_param: # Only future payment dates
                    payment_dates.append(temp_date)
            temp_date += relativedelta(months=1)
        else:
            break

    if maturity_date not in payment_dates and maturity_date > valuation_date_param:
        payment_dates.append(maturity_date)
    
    payment_dates = sorted(list(set(payment_dates)))

    for payment_date in payment_dates:
        is_interest_date = False
        if payment_interval_months > 0:
             if (payment_date.year * 12 + payment_date.month - (valuation_date_param.year * 12 + valuation_date_param.month)) % payment_interval_months == 0:
                 is_interest_date = True
        
        if is_interest_date:
            interest_amount = balance * (current_rate + (spread_bps / 10000.0 if rate_type == 'Floating' else 0.0)) * (payment_interval_months / 12.0)
            cash_flows.append({
                'instrument_id': instrument_id,
                'cashflow_date': payment_date,
                'amount': -interest_amount if category == 'Loan' else interest_amount,
                'type': 'Interest',
                'category': category,
                'rate_type': rate_type,
                'is_repricing_cashflow': False,
                'original_balance': balance
            })
        
        if payment_date == maturity_date:
            cash_flows.append({
                'instrument_id': instrument_id,
                'cashflow_date': maturity_date,
                'amount': -balance if category == 'Loan' else balance,
                'type': 'Principal',
                'category': category,
                'rate_type': rate_type,
                'is_repricing_cashflow': False,
                'original_balance': balance
            })
        
        if rate_type == 'Floating' and next_repricing_date is not None and payment_date >= next_repricing_date:
             if payment_date > valuation_date_param:
                cash_flows.append({
                    'instrument_id': instrument_id,
                    'cashflow_date': payment_date,
                    'amount': 0.0,
                    'type': 'Repricing',
                    'category': category,
                    'rate_type': rate_type,
                    'is_repricing_cashflow': True,
                    'original_balance': balance
                })
                if payment_interval_months > 0:
                    next_repricing_date += relativedelta(months=payment_interval_months)
                else:
                    next_repricing_date += relativedelta(years=1)
                
                if next_repricing_date > maturity_date:
                    next_repricing_date = maturity_date

    return pd.DataFrame(cash_flows)


def apply_behavioral_assumptions(cashflow_df_input, behavioral_flag, prepayment_rate_annual, nmd_beta, nmd_behavioral_maturity_years, valuation_date_param):
    """
    Applies behavioral assumptions (prepayment, NMD) to cash flows.
    """
    cashflow_df = cashflow_df_input.copy()
    if cashflow_df.empty:
        return pd.DataFrame([])

    if behavioral_flag == 'Mortgage_Prepayment' and 'Loan' in cashflow_df['category'].unique():
        principal_cfs_indices = cashflow_df[(cashflow_df['category'] == 'Loan') & (cashflow_df['type'] == 'Principal')].index
        
        for idx in principal_cfs_indices:
            original_principal_amount = cashflow_df.loc[idx, 'amount']
            cf_date = cashflow_df.loc[idx, 'cashflow_date']
            
            if cf_date > valuation_date_param:
                time_to_cf_years = (cf_date - valuation_date_param).days / 365.25
                prepayment_fraction = 1 - np.exp(-prepayment_rate_annual * time_to_cf_years)
                
                adjusted_principal_amount = original_principal_amount * (1 - prepayment_fraction)
                cashflow_df.loc[idx, 'amount'] = adjusted_principal_amount
                cashflow_df.loc[idx, 'type'] = 'Principal (Adj for Prepayment)'

    if behavioral_flag == 'NMD' and 'Deposit' in cashflow_df['category'].unique():
        instrument_id_nmd = cashflow_df['instrument_id'].iloc[0]
        initial_balance = cashflow_df['original_balance'].iloc[0]
        
        cashflow_df = pd.DataFrame([])
        
        behavioral_maturity_date = valuation_date_param + relativedelta(years=int(nmd_behavioral_maturity_years))
        stable_portion_amount = initial_balance * (1 - nmd_beta)

        if stable_portion_amount > 0:
            cashflow_df = pd.concat([cashflow_df, pd.DataFrame([{
                'instrument_id': instrument_id_nmd,
                'cashflow_date': behavioral_maturity_date,
                'amount': stable_portion_amount,
                'type': 'NMD Stable Principal',
                'category': 'Deposit',
                'rate_type': 'Fixed',
                'is_repricing_cashflow': False,
                'original_balance': stable_portion_amount
            }])], ignore_index=True)
        
    return cashflow_df.sort_values(by='cashflow_date').reset_index(drop=True)

@st.cache_data(show_spinner="Generating all cash flows...")
def generate_all_cash_flows(portfolio_df, baseline_date_curve_df, valuation_date_param,
                            prepayment_rate_annual_val, nmd_beta_val, nmd_behavioral_maturity_years_val):
    all_cash_flows_list = []
    
    for index, row in portfolio_df.iterrows():
        if row['is_core_NMD']:
             instrument_cash_flows = pd.DataFrame([{
                'instrument_id': row['instrument_id'],
                'cashflow_date': valuation_date_param,
                'amount': row['balance'],
                'type': 'Balance_NMD',
                'category': row['category'],
                'rate_type': row['rate_type'],
                'is_repricing_cashflow': False,
                'original_balance': row['balance']
            }])
        else:
            instrument_cash_flows = calculate_cashflows_for_instrument(row, baseline_date_curve_df, valuation_date_param)
        
        if not instrument_cash_flows.empty:
            adjusted_cash_flows = apply_behavioral_assumptions(
                instrument_cash_flows,
                row['behavioral_flag'],
                prepayment_rate_annual_val,
                nmd_beta_val,
                nmd_behavioral_maturity_years_val,
                valuation_date_param
            )
            all_cash_flows_list.append(adjusted_cash_flows)
    
    if not all_cash_flows_list:
        return pd.DataFrame()

    all_cash_flows = pd.concat(all_cash_flows_list, ignore_index=True)
    
    all_cash_flows = all_cash_flows[all_cash_flows['cashflow_date'] > valuation_date_param]
    
    return all_cash_flows.sort_values(by=['cashflow_date']).reset_index(drop=True)


@st.cache_data(show_spinner="Mapping cash flows to Basel buckets...")
def map_cashflows_to_basel_buckets(cashflow_df, valuation_date_param, basel_bucket_definitions):
    """
    Maps cash flows to defined Basel regulatory time buckets.
    """
    if cashflow_df.empty:
        return pd.DataFrame()

    bucketed_cfs_list = []

    for index, row in cashflow_df.iterrows():
        cf_date = row['cashflow_date']
        if isinstance(cf_date, date) and not isinstance(cf_date, datetime):
            cf_date = datetime.combine(cf_date, datetime.min.time())

        time_to_cf = relativedelta(cf_date, valuation_date_param)
        
        time_to_cf_total_months = time_to_cf.years * 12 + time_to_cf.months + (time_to_cf.days / 30.4375)
        
        bucket_label = 'Unbucketed'
        for start_val, end_val, unit in basel_bucket_definitions:
            lower_bound_months = start_val * 12 if unit == 'Y' else start_val
            upper_bound_months = end_val * 12 if unit == 'Y' else end_val
            
            if end_val == float('inf'):
                if time_to_cf_total_months >= lower_bound_months:
                    bucket_label = f"{start_val}{unit}-Over"
                    break
            elif lower_bound_months <= time_to_cf_total_months < upper_bound_months:
                bucket_label = f"{start_val}{unit}-{end_val}{unit}"
                break

        bucketed_cfs_list.append({
            'instrument_id': row['instrument_id'],
            'cashflow_date': row['cashflow_date'],
            'amount': row['amount'],
            'type': row['type'],
            'category': row['category'],
            'rate_type': row['rate_type'],
            'is_repricing_cashflow': row['is_repricing_cashflow'],
            'original_balance': row['original_balance'],
            'basel_bucket': bucket_label,
            'time_to_cf_months': time_to_cf_total_months
        })

    return pd.DataFrame(bucketed_cfs_list)

@st.cache_data(show_spinner="Calculating Present Values...")
def calculate_present_value_for_cashflows(cashflow_df, discount_date_curve_df, valuation_date_param):
    """
    Calculates the present value of cash flows using the provided discount curve.
    discount_date_curve_df must have 'date' and 'rate' columns, where 'date' is datetime.
    """
    if cashflow_df.empty or discount_date_curve_df.empty:
        return 0.0, 0.0

    cashflow_df['cashflow_date'] = pd.to_datetime(cashflow_df['cashflow_date'])
    discount_date_curve_df['date'] = pd.to_datetime(discount_date_curve_df['date'])

    relevant_discount_curve = discount_date_curve_df[discount_date_curve_df['date'] >= valuation_date_param].copy()
    
    if not relevant_discount_curve[relevant_discount_curve['date'] == valuation_date_param].empty:
        pass
    else:
        temp_row = pd.DataFrame([{'date': valuation_date_param, 'rate': 0.0}])
        relevant_discount_curve = pd.concat([relevant_discount_curve, temp_row]).drop_duplicates(subset='date').sort_values('date')

    relevant_discount_curve['days_from_val_date'] = (relevant_discount_curve['date'] - valuation_date_param).dt.days
    
    interpolation_points = relevant_discount_curve[relevant_discount_curve['days_from_val_date'] >= 0]

    if interpolation_points.empty or interpolation_points['days_from_val_date'].nunique() < 2:
        if not interpolation_points.empty:
            flat_rate = interpolation_points.iloc[0]['rate']
            interp_func = lambda days: np.array([flat_rate] * len(days))
        else:
            return 0.0, 0.0

    else:
        interp_func = interp1d(interpolation_points['days_from_val_date'], interpolation_points['rate'], 
                               kind='linear', fill_value="extrapolate")


    total_pv_assets = 0.0
    total_pv_liabilities = 0.0

    for index, row in cashflow_df.iterrows():
        cf_date = pd.to_datetime(row['cashflow_date'])
        cf_amount = row['amount']
        category = row['category']
        
        days_diff = (cf_date - valuation_date_param).days
        
        if days_diff < 0:
            continue

        discount_rate_at_cf_date = interp_func(days_diff).item()
        
        if days_diff == 0:
            discount_factor = 1.0
        else:
            time_in_years = days_diff / 365.25
            discount_factor = 1 / ((1 + discount_rate_at_cf_date)**time_in_years)

        pv_cf = cf_amount * discount_factor

        if category in ['Loan', 'Bond']:
            total_pv_assets += pv_cf
        elif category in ['Deposit']:
            total_pv_liabilities += pv_cf

    return total_pv_assets, total_pv_liabilities


def calculate_eve(pv_assets, pv_liabilities):
    """Calculates Economic Value of Equity (EVE)."""
    return pv_assets - pv_liabilities

@st.cache_data(show_spinner="Calculating Net Gap...")
def calculate_net_gap(bucketed_cashflow_df):
    """
    Calculates the net gap for each Basel bucket.
    """
    if bucketed_cashflow_df.empty:
        return pd.DataFrame()

    ordered_buckets = [
        '0M-1M', '1M-3M', '3M-6M', '6M-12M', '1Y-2Y', '2Y-3Y', '3Y-5Y', '5Y-10Y', '10Y-Over'
    ]
    
    asset_cfs = bucketed_cashflow_df[bucketed_cashflow_df['category'].isin(['Loan', 'Bond'])]
    liability_cfs = bucketed_cashflow_df[bucketed_cashflow_df['category'].isin(['Deposit'])]

    asset_sums = asset_cfs.groupby('basel_bucket')['amount'].sum().reindex(ordered_buckets).fillna(0)
    liability_sums = liability_cfs.groupby('basel_bucket')['amount'].sum().reindex(ordered_buckets).fillna(0)

    net_gap = asset_sums + liability_sums

    gap_table_df = pd.DataFrame({
        'Basel Bucket': net_gap.index,
        'Assets CF': asset_sums.values,
        'Liabilities CF': liability_sums.values,
        'Net Gap': net_gap.values
    })
    
    gap_table_df['Basel Bucket'] = pd.Categorical(gap_table_df['Basel Bucket'], categories=ordered_buckets, ordered=True)
    gap_table_df = gap_table_df.sort_values('Basel Bucket').fillna(0)

    return gap_table_df

@st.cache_data(show_spinner="Generating Basel shocked curve...")
def generate_basel_shocked_curve(baseline_curve, scenario_type, shock_magnitude_bps_short, shock_magnitude_bps_long):
    """
    Generates a shocked discount curve based on Basel scenarios.
    """
    shocked_curve = baseline_curve.copy()
    
    shock_short_decimal = shock_magnitude_bps_short / 10000.0
    shock_long_decimal = shock_magnitude_bps_long / 10000.0

    if shock_magnitude_bps_short == shock_magnitude_bps_long:
        shocked_curve['Discount_Rate'] = shocked_curve['Discount_Rate'] + shock_short_decimal
    else:
        short_tenor_point = standard_tenors_months[0]
        long_tenor_point = standard_tenors_months[-1]
        
        shock_tenors = [short_tenor_point, long_tenor_point]
        shock_values = [shock_short_decimal, shock_long_decimal]
        
        shock_interp_func = interp1d(shock_tenors, shock_values, kind='linear', fill_value='extrapolate')
        
        shock_amounts = shock_interp_func(shocked_curve['Tenor_Months'])
        
        shocked_curve['Discount_Rate'] = shocked_curve['Discount_Rate'] + shock_amounts
    
    return shocked_curve

def reprice_floating_instrument_cashflows_under_shock(instrument_cashflow_df, instrument_data, shocked_date_curve):
    """
    Reprices floating-rate instrument cash flows based on the shocked curve.
    This modifies the 'amount' of interest cash flows.
    """
    reprice_df = instrument_cashflow_df.copy()
    if reprice_df.empty:
        return pd.DataFrame([])

    if instrument_data['rate_type'] == 'Floating':
        spread_bps = instrument_data['spread_bps']
        
        shocked_date_curve['days_from_val_date'] = (shocked_date_curve['date'] - valuation_date).dt.days
        
        interpolation_points = shocked_date_curve[shocked_date_curve['days_from_val_date'] >= 0]

        if interpolation_points.empty or interpolation_points['days_from_val_date'].nunique() < 2:
            # st.warning("Insufficient unique points for shocked curve interpolation. Floating rates may not reprice correctly.")
            return reprice_df

        shocked_interp_func = interp1d(interpolation_points['days_from_val_date'], interpolation_points['rate'], 
                                       kind='linear', fill_value="extrapolate")

        interest_cfs_indices = reprice_df[(reprice_df['type'] == 'Interest') & (reprice_df['rate_type'] == 'Floating')].index
        
        for idx in interest_cfs_indices:
            cf_date = reprice_df.loc[idx, 'cashflow_date']
            original_balance = reprice_df.loc[idx, 'original_balance']
            
            days_diff = (cf_date - valuation_date).days
            if days_diff < 0: continue

            new_base_rate = shocked_interp_func(days_diff).item()
            new_effective_rate = new_base_rate + (spread_bps / 10000.0)

            freq_map = {'Monthly': 1, 'Quarterly': 3, 'Semi-Annually': 6, 'Annually': 12}
            payment_interval_months = freq_map.get(instrument_data['payment_freq'], 12)

            new_interest_amount = original_balance * (new_effective_rate / (12.0 / payment_interval_months))
            
            if instrument_data['category'] == 'Loan':
                reprice_df.loc[idx, 'amount'] = -new_interest_amount
            else:
                reprice_df.loc[idx, 'amount'] = new_interest_amount

    return reprice_df

def adjust_behavioral_assumptions_for_shock(cashflow_df, scenario_type, baseline_prepayment_rate, behavioral_shock_adjustment_factor):
    """
    Adjusts behavioral assumptions (e.g., prepayment rates) under shock scenarios.
    This function returns the adjusted prepayment rate to be used in re-calculating cash flows.
    """
    
    if 'Up' in scenario_type or 'Steepener' in scenario_type: # Rates up
        shocked_prepayment_rate = baseline_prepayment_rate * (1 - behavioral_shock_adjustment_factor)
    elif 'Down' in scenario_type or 'Flattener' in scenario_type: # Rates down
        shocked_prepayment_rate = baseline_prepayment_rate * (1 + behavioral_shock_adjustment_factor)
    else: # Unchanged or other scenarios
        shocked_prepayment_rate = baseline_prepayment_rate

    return shocked_prepayment_rate

@st.cache_data(show_spinner="Recalculating cash flows and PV for scenario...")
def recalculate_cashflows_and_pv_for_scenario(portfolio_df, shocked_date_curve, valuation_date_param, scenario_type,
                                            baseline_date_curve_df,
                                            baseline_prepayment_rate_annual, behavioral_shock_adjustment_factor,
                                            nmd_beta_val, nmd_behavioral_maturity_years_val):
    """
    Orchestrates the recalculation of cash flows and present values under a given shock scenario.
    """
    scenario_cash_flows_list = []

    adjusted_prepayment_rate_for_scenario = adjust_behavioral_assumptions_for_shock(
        pd.DataFrame([]),
        scenario_type,
        baseline_prepayment_rate_annual,
        behavioral_shock_adjustment_factor
    )

    for index, row in portfolio_df.iterrows():
        if row['is_core_NMD']:
             initial_instrument_cash_flows = pd.DataFrame([{
                'instrument_id': row['instrument_id'],
                'cashflow_date': valuation_date_param,
                'amount': row['balance'],
                'type': 'Balance_NMD',
                'category': row['category'],
                'rate_type': row['rate_type'],
                'is_repricing_cashflow': False,
                'original_balance': row['balance']
            }])
        else:
            initial_instrument_cash_flows = calculate_cashflows_for_instrument(row, baseline_date_curve_df, valuation_date_param)

        repriced_instrument_cash_flows = reprice_floating_instrument_cashflows_under_shock(
            initial_instrument_cash_flows, row, shocked_date_curve
        )

        behaviorally_adjusted_cash_flows = apply_behavioral_assumptions(
            repriced_instrument_cash_flows,
            row['behavioral_flag'],
            adjusted_prepayment_rate_for_scenario,
            nmd_beta_val,
            nmd_behavioral_maturity_years_val,
            valuation_date_param
        )
        
        scenario_cash_flows_list.append(behaviorally_adjusted_cash_flows)
    
    if not scenario_cash_flows_list:
        return 0.0

    all_scenario_cash_flows = pd.concat(scenario_cash_flows_list, ignore_index=True)
    
    all_scenario_cash_flows = all_scenario_cash_flows[all_scenario_cash_flows['cashflow_date'] > valuation_date_param]

    pv_assets_shocked, pv_liabilities_shocked = calculate_present_value_for_cashflows(
        all_scenario_cash_flows, shocked_date_curve, valuation_date_param
    )
    
    return calculate_eve(pv_assets_shocked, pv_liabilities_shocked)


def calculate_delta_eve(baseline_eve, shocked_eve):
    """Calculates Delta EVE."""
    return shocked_eve - baseline_eve

def report_delta_eve_as_percentage_of_tier1(delta_eve_results, tier1_capital):
    """
    Generates a DataFrame for Delta EVE report as percentage of Tier 1 Capital.
    delta_eve_results is a dictionary: {'Scenario Name': delta_eve_value, ...}
    """
    report_data = []
    for scenario, delta_eve_val in delta_eve_results.items():
        delta_eve_percent = (delta_eve_val / tier1_capital) * 100
        report_data.append({
            'Scenario': scenario,
            'Delta EVE (TWD)': delta_eve_val,
            'Delta EVE (% Tier 1 Capital)': delta_eve_percent
        })
    return pd.DataFrame(report_data)

