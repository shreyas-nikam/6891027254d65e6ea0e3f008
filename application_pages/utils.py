"""import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import uuid
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
import seaborn as sns
import pickle
import random
import streamlit as st
import plotly.express as px # Added for Plotly charts

# Global Constants/Parameters
valuation_date = datetime.today()

standard_tenors_months = [
    1, 3, 6, 12, 24, 36, 60, 120, 180, 240, 360 # Corresponding to 1M, 3M, 6M, 1Y, 2Y, 3Y, 5Y, 10Y, 15Y, 20Y, 30Y
]

market_rates_data = {
    '1M': 0.02, '3M': 0.022, '6M': 0.025, '1Y': 0.028, '2Y': 0.03, '3Y': 0.032,
    '5Y': 0.035, '7Y': 0.037, '10Y': 0.04, '15Y': 0.042, '20Y': 0.043, '30Y': 0.044
}

basel_bucket_definitions_list = [
    (0, 1, 'M'), (1, 3, 'M'), (3, 6, 'M'), (6, 12, 'M'),
    (1, 2, 'Y'), (2, 3, 'Y'), (3, 5, 'Y'), (5, 10, 'Y'), (10, float('inf'), 'Y')
]

shock_scenarios = {
    'Parallel Up': {'short': 200, 'long': 200},
    'Parallel Down': {'short': -200, 'long': -200},
    'Steepener': {'short': -100, 'long': 100},
    'Flattener': {'short': 100, 'long': -100},
    'Short-Up': {'short': 200, 'long': 0},
    'Short-Down': {'short': -200, 'long': 0}
}

# Utility Functions
def save_data_to_csv(dataframe, filename):
    dataframe.to_csv(filename, index=False)

def save_data_to_parquet(dataframe, filename):
    dataframe.to_parquet(filename, index=False)

def save_model_artifact(model_object, filename):
    with open(filename, 'wb') as f:
        pickle.dump(model_object, f)

def plot_delta_eve_bar_chart(delta_eve_percentages):
    fig = px.bar(
        delta_eve_percentages,
        x='Scenario',
        y='Delta EVE (% Tier 1 Capital)',
        color='Scenario',
        title='Delta EVE by Basel Interest Rate Shock Scenario',
        labels={'Delta EVE (% Tier 1 Capital)': 'Delta EVE (% of Tier 1 Capital)'}
    )
    fig.update_layout(xaxis_title="Scenario", yaxis_title="Delta EVE (% of Tier 1 Capital)")
    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig)

def convert_tenor_curve_to_date_curve(tenor_curve_df, valuation_date_for_conversion):
    date_curve_data = []
    for index, row in tenor_curve_df.iterrows():
        tenor_months = row['Tenor_Months']
        rate = row['Discount_Rate']
        target_date = valuation_date_for_conversion + relativedelta(months=tenor_months)
        date_curve_data.append({'date': target_date, 'rate': rate})
    return pd.DataFrame(date_curve_data)

# Data Generation and Initial Setup (functions used by pages)
@st.cache_data # Cache the generated portfolio
def generate_synthetic_portfolio(num_instruments, tier1_capital, start_date, end_date):
    data = []
    portfolio_as_of_date = datetime.strptime(start_date, "%Y-%m-%d").strftime("%Y-%m-%d")

    for _ in range(num_instruments):
        instrument_id = uuid.uuid4()
        category = random.choice(['Asset', 'Liability'])
        balance = round(random.uniform(1000, 1000000), 2)
        rate_type = random.choice(['Fixed', 'Floating'])
        index = random.choice(['TAIBOR', 'Fixed']) if rate_type == 'Floating' else 'N/A'
        spread_bps = random.randint(0, 100) if rate_type == 'Floating' else 0
        current_rate = round(random.uniform(0.01, 0.05), 4)
        payment_freq = random.choice([1, 3, 6, 12])

        maturity_date = (datetime.strptime(portfolio_as_of_date, '%Y-%m-%d') + relativedelta(months=random.randint(12, 360))).strftime('%Y-%m-%d')
        next_repricing_date = (datetime.strptime(portfolio_as_of_date, '%Y-%m-%d') + relativedelta(months=random.randint(1, 12))) if rate_type == 'Floating' else 'N/A'

        currency = 'TWD'
        embedded_option = random.choice(['None', 'Prepayment', 'Call', 'Put'])
        is_core_NMD = random.choice([True, False]) if category == 'Liability' else False
        behavioral_flag = 'Prepayment' if embedded_option == 'Prepayment' else is_core_NMD # Set flag for prepayment or NMD

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

    final_columns = [
        'instrument_id', 'category', 'balance', 'rate_type', 'index', 'spread_bps',
        'current_rate', 'payment_freq', 'maturity_date', 'next_repricing_date',
        'currency', 'embedded_option', 'is_core_NMD', 'behavioral_flag'
    ]
    df = pd.DataFrame(data).reindex(columns=final_columns)

    for col in ['maturity_date', 'next_repricing_date']:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: pd.to_datetime(x) if x != 'N/A' else None)
    return df

@st.cache_data # Cache the discount curve
def create_baseline_discount_curve(valuation_date_param, market_rates, tenors_in_months, liquidity_spread_bps):
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

# Cash Flow Generation and Pre-processing
def calculate_cashflows_for_instrument(instrument_data, baseline_curve, valuation_date_param):
    cash_flows = []
    instrument_id = instrument_data['instrument_id']
    category = instrument_data['category']
    balance = instrument_data['balance']
    rate_type = instrument_data['rate_type']
    current_rate = instrument_data['current_rate']
    payment_freq = instrument_data['payment_freq'] # In months
    maturity_date_dt = instrument_data['maturity_date']
    next_repricing_date_dt = instrument_data['next_repricing_date']

    if pd.isnull(maturity_date_dt):
        return pd.DataFrame() # No cash flows if no maturity date

    current_date_for_cf_gen = valuation_date_param.date() # Start from valuation date

    # Helper to get interpolated rate (using the provided discount curve)
    def get_discount_rate(target_date):
        tenor_days = (target_date - valuation_date_param.date()).days
        if tenor_days < 0:
            return 0.0 # Past cash flows are not discounted for future value

        # Convert discount curve to days for interpolation
        curve_days = [(valuation_date_param.date() + relativedelta(months=int(t))).days - valuation_date_param.date().days for t in baseline_curve['Tenor_Months']]
        curve_rates = baseline_curve['Discount_Rate'].tolist()

        if len(curve_days) < 2:
            return curve_rates[0] if curve_rates else 0.0 # Fallback

        interpolator = interp1d(curve_days, curve_rates, kind='linear', fill_value='extrapolate')
        rate = interpolator(tenor_days).item()
        return max(0.0, rate) # Ensure non-negative rates

    # Generate cash flows up to maturity
    if payment_freq > 0:
        # Determine the first payment date after the valuation date
        first_payment_date = current_date_for_cf_gen + relativedelta(months=payment_freq)
        while first_payment_date <= maturity_date_dt.date():
            rate_applied = current_rate # Start with current rate
            if rate_type == 'Floating' and next_repricing_date_dt is not None and first_payment_date >= next_repricing_date_dt.date():
                 # In a real model, this would be based on forward rates or a new index rate look-up
                 # For simplicity, we assume the rate for floating is dynamically updated from current_rate.
                pass # The rate_applied will be handled in shock revaluation

            cf_amount = balance * rate_applied * (payment_freq / 12.0) # Simple interest calculation

            cash_flows.append({
                'instrument_id': instrument_id,
                'category': category,
                'cash_flow_date': first_payment_date,
                'amount': cf_amount,
                'type': 'Interest',
                'balance_at_cf': balance,
                'discount_rate': get_discount_rate(first_payment_date),
                'rate_type': rate_type,
                'is_core_NMD': instrument_data['is_core_NMD'],
                'behavioral_flag': instrument_data['behavioral_flag'] # Pass behavioral flag to CFs
            })
            first_payment_date += relativedelta(months=payment_freq)

    # Add principal repayment at maturity
    cash_flows.append({
        'instrument_id': instrument_id,
        'category': category,
        'cash_flow_date': maturity_date_dt.date(),
        'amount': balance, # Principal repayment
        'type': 'Principal',
        'balance_at_cf': 0,
        'discount_rate': get_discount_rate(maturity_date_dt.date()),
        'rate_type': rate_type,
        'is_core_NMD': instrument_data['is_core_NMD'],
        'behavioral_flag': instrument_data['behavioral_flag']
    })

    df_cf = pd.DataFrame(cash_flows)
    if not df_cf.empty:
        df_cf['pv'] = df_cf.apply(
            lambda row: row['amount'] / (1 + row['discount_rate']) ** ((row['cash_flow_date'] - valuation_date_param.date()).days / 365.25)
            if (row['cash_flow_date'] - valuation_date_param.date()).days >= 0
            else 0, axis=1
        )
    return df_cf

def apply_behavioral_assumptions(cashflow_df, behavioral_flag_instrument, prepayment_rate_annual, nmd_beta, nmd_behavioral_maturity_years, valuation_date_param):
    if cashflow_df.empty:
        return cashflow_df

    modified_cashflow_df = cashflow_df.copy()

    # Mortgage Prepayment (for assets with 'Prepayment' option)
    if behavioral_flag_instrument == 'Prepayment':
        # Simple prepayment: Reduce future principal cash flows
        principal_cfs_idx = modified_cashflow_df[(modified_cashflow_df['type'] == 'Principal') & (modified_cashflow_df['cash_flow_date'] > valuation_date_param.date())].index
        for idx in principal_cfs_idx:
            row = modified_cashflow_df.loc[idx]
            time_to_maturity_years = (row['cash_flow_date'] - valuation_date_param.date()).days / 365.25
            reduction_factor = time_to_maturity_years * prepayment_rate_annual
            modified_cashflow_df.loc[idx, 'amount'] *= (1 - min(reduction_factor, 1.0))

    # NMD (Non-Maturity Deposits) behavioral maturity
    if behavioral_flag_instrument is True and 'is_core_NMD' in modified_cashflow_df.columns and modified_cashflow_df['is_core_NMD'].any():
        nmd_principal_cfs = modified_cashflow_df[(modified_cashflow_df['type'] == 'Principal') & (modified_cashflow_df['is_core_NMD'])].copy()
        if not nmd_principal_cfs.empty:
            original_principal_idx = nmd_principal_cfs.index[0] # Assuming one principal CF per NMD instrument
            original_amount = modified_cashflow_df.loc[original_principal_idx, 'amount']
            original_cash_flow_date = modified_cashflow_df.loc[original_principal_idx, 'cash_flow_date']

            behavioral_maturity_date = valuation_date_param.date() + relativedelta(years=int(nmd_behavioral_maturity_years))

            if behavioral_maturity_date > original_cash_flow_date:
                behavioral_amount = original_amount * nmd_beta
                remaining_amount = original_amount * (1 - nmd_beta)

                modified_cashflow_df.loc[original_principal_idx, 'amount'] = remaining_amount

                # Add new principal cash flow at behavioral maturity date
                new_principal_cf = {
                    'instrument_id': modified_cashflow_df.loc[original_principal_idx, 'instrument_id'],
                    'category': modified_cashflow_df.loc[original_principal_idx, 'category'],
                    'cash_flow_date': behavioral_maturity_date,
                    'amount': behavioral_amount,
                    'type': 'Principal',
                    'balance_at_cf': 0,
                    'discount_rate': 0.0, # Will be re-calculated during PV
                    'rate_type': modified_cashflow_df.loc[original_principal_idx, 'rate_type'],
                    'is_core_NMD': True,
                    'behavioral_flag': True
                }
                modified_cashflow_df = pd.concat([modified_cashflow_df, pd.DataFrame([new_principal_cf])], ignore_index=True)

    return modified_cashflow_df.sort_values(by='cash_flow_date').reset_index(drop=True)

@st.cache_data(show_spinner="Calculating cash flows...")
def generate_all_cash_flows(portfolio_df, baseline_date_curve_df, valuation_date_param,
                            prepayment_rate_annual_val, nmd_beta_val, nmd_behavioral_maturity_years_val):
    all_cash_flows_list = []
    for index, row in portfolio_df.iterrows():
        instrument_cash_flows = calculate_cashflows_for_instrument(row, baseline_date_curve_df, valuation_date_param)
        if not instrument_cash_flows.empty:
            adjusted_cash_flows = apply_behavioral_assumptions(
                instrument_cash_flows,
                row['behavioral_flag'], # Pass the specific behavioral flag from the instrument
                prepayment_rate_annual_val,
                nmd_beta_val,
                nmd_behavioral_maturity_years_val,
                valuation_date_param
            )
            all_cash_flows_list.append(adjusted_cash_flows)
    if all_cash_flows_list:
        return pd.concat(all_cash_flows_list, ignore_index=True)
    else:
        return pd.DataFrame()


@st.cache_data(show_spinner="Mapping cash flows to Basel buckets...")
def map_cashflows_to_basel_buckets(cashflow_df, valuation_date_param, basel_bucket_definitions):
    if cashflow_df.empty:
        return pd.DataFrame()

    bucketed_data = []

    for _, row in cashflow_df.iterrows():
        cf_date = row['cash_flow_date']
        tenor_days = (cf_date - valuation_date_param.date()).days
        tenor_months = tenor_days / 30.44  # Approximate months
        tenor_years = tenor_days / 365.25 # Approximate years

        bucket_name = 'Uncategorized'
        for min_val, max_val, unit in basel_bucket_definitions:
            if unit == 'M':
                if min_val <= tenor_months < max_val:
                    bucket_name = f"{min_val}-{max_val}M"
                    break
            elif unit == 'Y':
                if max_val == float('inf'):
                    if tenor_years >= min_val:
                        bucket_name = f"{min_val}Y+"
                        break
                elif min_val <= tenor_years < max_val:
                    bucket_name = f"{min_val}-{max_val}Y"
                    break
        bucketed_data.append({
            'instrument_id': row['instrument_id'],
            'category': row['category'],
            'cash_flow_date': row['cash_flow_date'],
            'amount': row['amount'],
            'type': row['type'],
            'pv': row['pv'],
            'bucket': bucket_name,
            'behavioral_flag': row['behavioral_flag'] # Ensure this is passed through
        })
    return pd.DataFrame(bucketed_data)


# Baseline EVE Calculation and Gap Analysis
@st.cache_data(show_spinner="Calculating Present Value for cash flows...")
def calculate_present_value_for_cashflows(cashflow_df, discount_curve_df, valuation_date_param):
    if cashflow_df.empty:
        return 0.0, 0.0 # pv_assets, pv_liabilities

    pv_assets = 0.0
    pv_liabilities = 0.0

    # Create an interpolation function for discount rates based on date
    # This assumes discount_curve_df is sorted by Tenor_Months
    tenor_dates = [valuation_date_param.date() + relativedelta(months=int(t)) for t in discount_curve_df['Tenor_Months']]
    discount_rates = discount_curve_df['Discount_Rate'].tolist()

    if len(tenor_dates) < 2: # Need at least 2 points for interpolation
        # Fallback if curve is too short, might happen in very specific test cases
        interpolator = lambda d: discount_rates[0] if discount_rates else 0.0
    else:
        # Convert dates to days since valuation_date for interpolation
        days_since_val_date = [(td - valuation_date_param.date()).days for td in tenor_dates]
        interpolator = interp1d(days_since_val_date, discount_rates, kind='linear', fill_value='extrapolate')

    for _, row in cashflow_df.iterrows():
        cf_date = row['cash_flow_date']
        amount = row['amount']
        category = row['category']

        if cf_date < valuation_date_param.date():
            continue # Skip past cash flows

        time_to_cf_days = (cf_date - valuation_date_param.date()).days

        if time_to_cf_days == 0 and len(discount_rates) > 0: # If it's today, use the closest short rate or 0 if no short rate
            discount_rate = discount_rates[0] if discount_rates else 0.0
        else:
            discount_rate = interpolator(time_to_cf_days).item() # Use .item() to get scalar from numpy array

        discount_rate = max(0.0, discount_rate) # Prevent negative rates

        # Ensure that (1 + discount_rate) is not zero or negative for PV calculation
        if (1 + discount_rate) <= 0:
            pv_factor = 0 # Avoid division by zero/negative
        else:
            pv_factor = (1 + discount_rate) ** (time_to_cf_days / 365.25)

        present_value = amount / pv_factor if pv_factor != 0 else 0

        if category == 'Asset':
            pv_assets += present_value
        elif category == 'Liability':
            pv_liabilities += present_value

    return pv_assets, pv_liabilities

def calculate_eve(pv_assets, pv_liabilities):
    return pv_assets - pv_liabilities

@st.cache_data(show_spinner="Calculating Net Gap...")
def calculate_net_gap(bucketed_cashflow_df):
    if bucketed_cashflow_df.empty:
        return pd.DataFrame(columns=['Bucket', 'Asset Cash Flows', 'Liability Cash Flows', 'Net Gap'])

    # Aggregate cash flows by bucket and category
    grouped_cf = bucketed_cashflow_df.groupby(['bucket', 'category'])['amount'].sum().unstack(fill_value=0)

    # Ensure 'Asset' and 'Liability' columns exist, even if empty
    if 'Asset' not in grouped_cf.columns:
        grouped_cf['Asset'] = 0
    if 'Liability' not in grouped_cf.columns:
        grouped_cf['Liability'] = 0

    net_gap_df = pd.DataFrame({
        'Asset Cash Flows': grouped_cf['Asset'],
        'Liability Cash Flows': grouped_cf['Liability']
    })
    net_gap_df['Net Gap'] = net_gap_df['Asset Cash Flows'] - net_gap_df['Liability Cash Flows']
    net_gap_df = net_gap_df.reset_index().rename(columns={'index': 'Bucket'})

    # Order buckets based on predefined Basel bucket order
    ordered_buckets = [
        "0-1M", "1-3M", "3-6M", "6-12M",
        "1-2Y", "2-3Y", "3-5Y", "5-10Y", "10Y+"
    ]
    # Filter for only defined buckets and reorder
    net_gap_df['Bucket_Order'] = pd.Categorical(net_gap_df['Bucket'], categories=ordered_buckets, ordered=True)
    net_gap_df = net_gap_df.sort_values('Bucket_Order').drop('Bucket_Order', axis=1)

    return net_gap_df

# Scenario Shock Application and Revaluation
@st.cache_data # Cache shocked curve generation
def generate_basel_shocked_curve(baseline_curve_df, scenario_type, shock_magnitude_bps_short, shock_magnitude_bps_long):
    shocked_curve_data = []
    # Convert bps to decimal
    shock_short_decimal = shock_magnitude_bps_short / 10000.0
    shock_long_decimal = shock_magnitude_bps_long / 10000.0

    for index, row in baseline_curve_df.iterrows():
        tenor_months = row['Tenor_Months']
        baseline_rate = row['Discount_Rate']

        # Define short vs. long tenor threshold (e.g., 1 year or 12 months)
        # Basel defines short as <= 1 year, and long as > 1 year.
        if tenor_months <= 12: # Short end of the curve
            shocked_rate = baseline_rate + shock_short_decimal
        else: # Long end of the curve
            shocked_rate = baseline_rate + shock_long_decimal

        shocked_curve_data.append({
            'Tenor_Months': tenor_months,
            'Discount_Rate': shocked_rate
        })
    return pd.DataFrame(shocked_curve_data)


def reprice_floating_instrument_cashflows_under_shock(instrument_cashflow_df, instrument_data, shocked_date_curve, valuation_date_param):
    if instrument_cashflow_df.empty or instrument_data['rate_type'] != 'Floating':
        return instrument_cashflow_df.copy()

    repriced_cashflows = instrument_cashflow_df.copy()

    # Create an interpolation function for shocked discount rates based on date for repricing
    shocked_tenor_dates_for_interp = shocked_date_curve['date'].tolist()
    shocked_discount_rates_for_interp = shocked_date_curve['rate'].tolist()

    if len(shocked_tenor_dates_for_interp) < 2:
        reprice_interpolator = lambda d: shocked_discount_rates_for_interp[0] if shocked_discount_rates_for_interp else 0.0
    else:
        # Convert dates to days since valuation_date for interpolation
        days_since_val_date_for_interp = [(td.date() - valuation_date_param.date()).days for td in shocked_tenor_dates_for_interp]
        reprice_interpolator = interp1d(days_since_val_date_for_interp, shocked_discount_rates_for_interp, kind='linear', fill_value='extrapolate')

    for index, row in repriced_cashflows.iterrows():
        if row['rate_type'] == 'Floating' and instrument_data['next_repricing_date'] is not None and row['cash_flow_date'] >= instrument_data['next_repricing_date'].date():
            # Get the new rate from the shocked curve for the relevant tenor/date
            cf_date = row['cash_flow_date']
            time_to_cf_days = (cf_date - valuation_date_param.date()).days

            shocked_rate_at_cf_date = reprice_interpolator(time_to_cf_days).item()
            shocked_rate_at_cf_date = max(0.0, shocked_rate_at_cf_date) # Ensure non-negative

            # Apply the new shocked rate + original spread
            new_rate_applied = shocked_rate_at_cf_date + (instrument_data['spread_bps'] / 10000.0)

            # Recalculate interest cash flow assuming balance at CF is still valid for this instrument
            payment_freq_months = instrument_data['payment_freq']
            # Use the balance from the cashflow row which would be the remaining balance if principal was paid
            repriced_cashflows.loc[index, 'amount'] = row['balance_at_cf'] * new_rate_applied * (payment_freq_months / 12.0) if row['balance_at_cf'] > 0 else 0
            repriced_cashflows.loc[index, 'current_rate'] = new_rate_applied # Update for consistency

    return repriced_cashflows

def adjust_behavioral_assumptions_for_shock(cashflow_df, scenario_type, baseline_prepayment_rate, behavioral_shock_adjustment_factor, valuation_date_param):
    if cashflow_df.empty:
        return cashflow_df.copy()

    adjusted_cashflow_df = cashflow_df.copy()

    # Adjust prepayment rate based on scenario
    adjusted_prepayment_rate = baseline_prepayment_rate
    if scenario_type in ['Parallel Up', 'Short-Up']:
        adjusted_prepayment_rate = baseline_prepayment_rate * (1 - behavioral_shock_adjustment_factor)
    elif scenario_type in ['Parallel Down', 'Short-Down']:
        adjusted_prepayment_rate = baseline_prepayment_rate * (1 + behavioral_shock_adjustment_factor)

    # Re-apply prepayment logic for 'Prepayment' behavioral flag
    prepayment_cfs_idx = adjusted_cashflow_df[(adjusted_cashflow_df['behavioral_flag'] == 'Prepayment') & (adjusted_cashflow_df['type'] == 'Principal') & (adjusted_cashflow_df['cash_flow_date'] > valuation_date_param.date())].index
    for idx in prepayment_cfs_idx:
        row = adjusted_cashflow_df.loc[idx]
        time_to_maturity_years = (row['cash_flow_date'] - valuation_date_param.date()).days / 365.25
        reduction_factor = time_to_maturity_years * adjusted_prepayment_rate
        adjusted_cashflow_df.loc[idx, 'amount'] = row['amount'] * (1 - min(reduction_factor, 1.0)) # Apply reduction to existing amount

    return adjusted_cashflow_df


@st.cache_data(show_spinner="Recalculating cash flows and PV for scenario...")
def recalculate_cashflows_and_pv_for_scenario(portfolio_df, shocked_curve_df, valuation_date_param, scenario_type,
                                            baseline_date_curve_df, # Pass baseline for initial CF generation
                                            prepayment_rate_annual_for_shock, behavioral_shock_adjustment_factor,
                                            nmd_beta_val, nmd_behavioral_maturity_years_val):
    all_cash_flows_shocked = pd.DataFrame()
    shocked_date_curve = convert_tenor_curve_to_date_curve(shocked_curve_df, valuation_date_param)

    for index, row in portfolio_df.iterrows():
        # Start with fresh cash flows for each instrument from baseline conditions
        instrument_cash_flows_initial = calculate_cashflows_for_instrument(row, baseline_date_curve_df, valuation_date_param)

        # Apply behavioral adjustments under shock scenario
        instrument_cash_flows_adjusted_behavior = adjust_behavioral_assumptions_for_shock(
            instrument_cash_flows_initial,
            scenario_type,
            prepayment_rate_annual_for_shock,
            behavioral_shock_adjustment_factor,
            valuation_date_param
        )

        # Reprice floating rate cash flows using the shocked curve
        instrument_cash_flows_repriced = reprice_floating_instrument_cashflows_under_shock(
            instrument_cash_flows_adjusted_behavior,
            row,
            shocked_date_curve,
            valuation_date_param
        )
        all_cash_flows_shocked = pd.concat([all_cash_flows_shocked, instrument_cash_flows_repriced], ignore_index=True)

    # Recalculate PV using the shocked curve (passed as shocked_curve_df)
    pv_assets_shocked, pv_liabilities_shocked = calculate_present_value_for_cashflows(
        all_cash_flows_shocked, shocked_curve_df, valuation_date_param
    )
    return calculate_eve(pv_assets_shocked, pv_liabilities_shocked)


# Delta EVE Reporting and Model Persistence
def calculate_delta_eve(baseline_eve, shocked_eve):
    return shocked_eve - baseline_eve

def report_delta_eve_as_percentage_of_tier1(delta_eve_results, tier1_capital):
    report_data = []
    for scenario, delta_eve_value in delta_eve_results.items():
        if tier1_capital > 0:
            percentage = (delta_eve_value / tier1_capital) * 100
        else:
            percentage = 0.0 # Handle division by zero

        report_data.append({
            'Scenario': scenario,
            'Delta EVE (TWD)': delta_eve_value,
            'Delta EVE (% Tier 1 Capital)': percentage
        })
    return pd.DataFrame(report_data)
""")