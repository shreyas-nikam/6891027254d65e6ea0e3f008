import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import uuid
from scipy.interpolate import interp1d
import plotly.graph_objects as go # Changed from matplotlib to plotly
import random
import streamlit as st

# --- Constants ---
market_rates_data = {
    "1M": 0.015,
    "3M": 0.018,
    "6M": 0.020,
    "1Y": 0.022,
    "2Y": 0.025,
    "3Y": 0.027,
    "5Y": 0.030,
    "7Y": 0.032,
    "10Y": 0.035,
    "15Y": 0.037,
    "20Y": 0.038,
    "30Y": 0.040,
}

standard_tenors_months = {
    "1M": 1, "3M": 3, "6M": 6, "1Y": 12, "2Y": 24, "3Y": 36,
    "5Y": 60, "7Y": 84, "10Y": 120, "15Y": 180, "20Y": 240, "30Y": 360
}

basel_bucket_definitions_list = [
    {"bucket": "0-1M", "min_months": 0, "max_months": 1},
    {"bucket": "1M-3M", "min_months": 1, "max_months": 3},
    {"bucket": "3M-6M", "min_months": 3, "max_months": 6},
    {"bucket": "6M-1Y", "min_months": 6, "max_months": 12},
    {"bucket": "1Y-2Y", "min_months": 12, "max_months": 24},
    {"bucket": "2Y-3Y", "min_months": 24, "max_months": 36},
    {"bucket": "3Y-4Y", "min_months": 36, "max_months": 48},
    {"bucket": "4Y-5Y", "min_months": 48, "max_months": 60},
    {"bucket": "5Y-7Y", "min_months": 60, "max_months": 84},
    {"bucket": "7Y-10Y", "min_months": 84, "max_months": 120},
    {"bucket": "10Y-15Y", "min_months": 120, "max_months": 180},
    {"bucket": "15Y-20Y", "min_months": 180, "max_months": 240},
    {"bucket": "20Y+", "min_months": 240, "max_months": float('inf')},
]

shock_scenarios = {
    "Parallel Up": {"short": 200, "long": 200}, # Example magnitudes in bps
    "Parallel Down": {"short": -200, "long": -200},
    "Steepener": {"short": -50, "long": 100},
    "Flattener": {"short": 100, "long": -50},
    "Short Rate Up": {"short": 200, "long": 0},
    "Short Rate Down": {"short": -200, "long": 0},
}


# --- Utility Functions ---

@st.cache_data
def generate_synthetic_portfolio(num_instruments, tier1_capital, start_date, end_date):
    instrument_types = ["Loan", "Deposit", "Bond", "Mortgage", "Swap"]
    rate_types = ["Fixed", "Floating", "Hybrid"]
    payment_frequencies = ["Monthly", "Quarterly", "Semi-Annually", "Annually"]
    currencies = ["TWD"]

    portfolio_data = []
    for _ in range(num_instruments):
        instrument_id = str(uuid.uuid4())
        instrument_type = random.choice(instrument_types)
        is_asset = True if instrument_type in ["Loan", "Bond", "Mortgage"] else False # Deposits are liabilities
        
        issue_date = start_date + timedelta(days=random.randint(0, (end_date - start_date).days // 2))
        maturity_date = issue_date + timedelta(days=random.randint(365, (end_date - issue_date).days))
        
        amount = random.randint(1_000_000, 100_000_000)
        
        rate_type = random.choice(rate_types)
        coupon_rate = round(random.uniform(0.01, 0.05), 4) # 1% to 5%
        if instrument_type == "Deposit": # Deposits typically have lower rates
            coupon_rate = round(random.uniform(0.005, 0.02), 4)
        
        payment_frequency = random.choice(payment_frequencies)
        currency = random.choice(currencies)

        specific_features = {}
        if instrument_type == "Mortgage":
            specific_features["prepayment_option"] = True
        elif instrument_type == "Deposit" and random.random() < 0.5: # 50% chance of NMD
            specific_features["nmd_flag"] = True
        elif instrument_type == "Swap":
            # For simplicity, assume one leg is fixed and the other floating referencing a market rate
            # We'll use a generic "floating_spread" for the floating leg for now
            specific_features["floating_spread"] = round(random.uniform(-0.001, 0.001), 4) # +/- 10 bps
            rate_type = "Hybrid" # Swaps are often hybrid in nature

        portfolio_data.append({
            "Instrument_ID": instrument_id,
            "Instrument_Type": instrument_type,
            "Is_Asset": is_asset,
            "Issue_Date": issue_date,
            "Maturity_Date": maturity_date,
            "Amount": amount,
            "Rate_Type": rate_type,
            "Coupon_Rate": coupon_rate,
            "Payment_Frequency": payment_frequency,
            "Currency": currency,
            "Specific_Features": specific_features
        })
    df = pd.DataFrame(portfolio_data)
    # Ensure date columns are datetime objects
    df["Issue_Date"] = pd.to_datetime(df["Issue_Date"])
    df["Maturity_Date"] = pd.to_datetime(df["Maturity_Date"])
    return df

def plot_delta_eve_bar_chart(delta_eve_percentages):
    scenarios = list(delta_eve_percentages.keys())
    percentages = list(delta_eve_percentages.values())

    fig = go.Figure(data=[
        go.Bar(x=scenarios, y=percentages,
               marker_color=['red' if p < 0 else 'green' for p in percentages])
    ])
    fig.update_layout(
        title="ΔEVE by Basel Interest Rate Shock Scenario (% of Tier 1 Capital)",
        xaxis_title="Scenario",
        yaxis_title="ΔEVE (% of Tier 1 Capital)",
        title_x=0.5,
        plot_bgcolor='white'
    )
    return fig

@st.cache_data
def create_baseline_discount_curve(valuation_date, market_rates, tenors_in_months, liquidity_spread_bps):
    rates_list = []
    for tenor_label, months in tenors_in_months.items():
        rate = market_rates[tenor_label]
        rates_list.append({"Tenor": tenor_label, "Months_to_Maturity": months, "Rate_Annual": rate})

    rates_df = pd.DataFrame(rates_list)
    rates_df["rate_decimal"] = rates_df["Rate_Annual"] + (liquidity_spread_bps / 10000.0)

    # Ensure 0 months to maturity has a rate (e.g., current spot rate or first available rate)
    # For interpolation, it's good to have a starting point at time 0
    if 0 not in rates_df["Months_to_Maturity"].values:
        # If no 0-month tenor, use the 1M rate as the spot rate for simplicity, or interpolate
        # Let's add a 0-month tenor with the 1M rate or a reasonable proxy
        rates_df = pd.concat([pd.DataFrame([{"Tenor": "0M", "Months_to_Maturity": 0, "Rate_Annual": rates_df.loc[rates_df["Months_to_Maturity"] == 1]["Rate_Annual"].iloc[0], "rate_decimal": rates_df.loc[rates_df["Months_to_Maturity"] == 1]["rate_decimal"].iloc[0]}]), rates_df]).reset_index(drop=True)


    max_months = rates_df["Months_to_Maturity"].max()
    rates_df = rates_df.sort_values(by="Months_to_Maturity")

    rates_for_interp_x = rates_df["Months_to_Maturity"].tolist()
    rates_for_interp_y = rates_df["rate_decimal"].tolist()

    f_interp = interp1d(rates_for_interp_x, rates_for_interp_y, kind="linear", fill_value="extrapolate")

    # Generate rates for each month from 0 up to the maximum tenor
    all_months = np.arange(0, max_months + 1)
    interpolated_rates = f_interp(all_months)

    baseline_curve_df = pd.DataFrame({
        "Months_to_Maturity": all_months,
        "Rate": interpolated_rates,
    })
    baseline_curve_df["Valuation_Date"] = valuation_date
    return baseline_curve_df

@st.cache_data
def convert_tenor_curve_to_date_curve(tenor_curve_df, valuation_date_for_conversion):
    date_curve_data = []
    for _, row in tenor_curve_df.iterrows():
        months = row["Months_to_Maturity"]
        rate = row["Rate"]
        # Calculate the actual date based on valuation_date_for_conversion
        curve_date = valuation_date_for_conversion + relativedelta(months=int(months))
        date_curve_data.append({
            "Curve_Date": curve_date,
            "Rate": rate,
            "Months_to_Maturity": months, # Keep for consistency/debug
            "Valuation_Date": valuation_date_for_conversion
        })
    return pd.DataFrame(date_curve_data)


@st.cache_data
def calculate_cashflows_for_instrument(instrument_data, baseline_curve):
    instrument_id = instrument_data["Instrument_ID"]
    issue_date = instrument_data["Issue_Date"]
    maturity_date = instrument_data["Maturity_Date"]
    amount = instrument_data["Amount"]
    rate_type = instrument_data["Rate_Type"]
    coupon_rate = instrument_data["Coupon_Rate"]
    payment_frequency = instrument_data["Payment_Frequency"]
    is_asset = instrument_data["Is_Asset"]
    specific_features = instrument_data["Specific_Features"]
    instrument_type = instrument_data["Instrument_Type"] # Added for clarity in logic

    cashflows = []

    # Determine payment frequency in months
    if payment_frequency == "Monthly":
        freq_months = 1
    elif payment_frequency == "Quarterly":
        freq_months = 3
    elif payment_frequency == "Semi-Annually":
        freq_months = 6
    elif payment_frequency == "Annually":
        freq_months = 12
    else:
        freq_months = 12 # Default


    # Starting from the issue date, project cash flows
    current_date = issue_date

    # Initial cash flow (e.g., loan disbursement (asset), deposit receipt (liability), bond purchase (asset))
    # This is typically at issue date, representing the principal in or out
    cashflows.append({
        "Instrument_ID": instrument_id,
        "Cashflow_Date": issue_date,
        "Cashflow_Amount": -amount if is_asset else amount, # Negative for asset disbursement, positive for liability receipt
        "Type": "Principal Initial"
    })

    # Generate coupon/interest payments
    while current_date <= maturity_date:
        # Ensure we don't double count initial cash flow date for interest if it's a payment date
        if current_date > issue_date: # Only generate interest payments *after* the initial funding
            # Calculate period interest
            if rate_type == "Fixed":
                interest_payment = amount * coupon_rate * (freq_months / 12)
            elif rate_type == "Floating":
                # For floating rates, get the rate from the baseline curve for the remaining tenor
                # This requires knowing the valuation date for 'Months_to_Maturity' mapping
                valuation_date_for_cfs = baseline_curve["Valuation_Date"].iloc[0] # Assuming this is consistent
                
                # Calculate months from valuation date to the current payment date
                time_delta_days = (current_date - valuation_date_for_cfs).days
                months_to_payment = round(time_delta_days / 30.44) # Approximate months
                months_to_payment = max(0, months_to_payment) # Cannot be negative


                # Interpolate rate from the baseline curve
                if not baseline_curve.empty:
                    # Ensure the interpolation function covers the range of months_to_payment
                    min_m = baseline_curve["Months_to_Maturity"].min()
                    max_m = baseline_curve["Months_to_Maturity"].max()
                    
                    if months_to_payment < min_m:
                        current_market_rate = baseline_curve[baseline_curve["Months_to_Maturity"] == min_m]["Rate"].iloc[0]
                    elif months_to_payment > max_m:
                        current_market_rate = baseline_curve[baseline_curve["Months_to_Maturity"] == max_m]["Rate"].iloc[0]
                    else:
                        interp_func = interp1d(
                            baseline_curve["Months_to_Maturity"],
                            baseline_curve["Rate"],
                            kind="linear",
                            fill_value="extrapolate" # This ensures it works outside bounds too
                        )
                        current_market_rate = interp_func(months_to_payment).item()
                else:
                    current_market_rate = 0.0 # Fallback if curve is empty


                interest_payment = amount * current_market_rate * (freq_months / 12)
                
            elif rate_type == "Hybrid" and instrument_type == "Swap":
                # Assuming a "pay fixed, receive floating" or "pay floating, receive fixed" swap
                # For baseline, let's simplify and assume the net interest represents the floating leg
                # If we consider it as a liability where bank pays floating:
                # amount * (floating_rate + floating_spread) - amount * fixed_rate
                # For a generic "interest" cashflow, we'll use the floating rate at that tenor
                
                valuation_date_for_cfs = baseline_curve["Valuation_Date"].iloc[0]
                time_delta_days = (current_date - valuation_date_for_cfs).days
                months_to_payment = round(time_delta_days / 30.44)
                months_to_payment = max(0, months_to_payment)
                
                if not baseline_curve.empty:
                    min_m = baseline_curve["Months_to_Maturity"].min()
                    max_m = baseline_curve["Months_to_Maturity"].max()
                    if months_to_payment < min_m:
                        current_market_rate = baseline_curve[baseline_curve["Months_to_Maturity"] == min_m]["Rate"].iloc[0]
                    elif months_to_payment > max_m:
                        current_market_rate = baseline_curve[baseline_curve["Months_to_Maturity"] == max_m]["Rate"].iloc[0]
                    else:
                        interp_func = interp1d(
                            baseline_curve["Months_to_Maturity"],
                            baseline_curve["Rate"],
                            kind="linear",
                            fill_value="extrapolate"
                        )
                        current_market_rate = interp_func(months_to_payment).item()
                else:
                    current_market_rate = 0.0

                floating_spread = specific_features.get("floating_spread", 0.0)
                adjusted_rate = current_market_rate + floating_spread
                
                # For a swap, the amount is usually not exchanged, but rather the notional.
                # The cash flow is the net interest.
                # For simplicity of cash flow generation, let's assume `coupon_rate` is the baseline rate.
                # The floating re-pricing will handle the shock part.
                interest_payment = amount * coupon_rate * (freq_months / 12)
                
            else:
                interest_payment = 0 # For NMDs, etc., handled by behavioral model

            cashflows.append({
                "Instrument_ID": instrument_id,
                "Cashflow_Date": current_date,
                "Cashflow_Amount": interest_payment if is_asset else -interest_payment,
                "Type": "Interest"
            })
        current_date += relativedelta(months=freq_months)

    # Add principal repayment/receipt at maturity
    # This is often the reversal of the initial principal cash flow
    if amount > 0: # Ensure amount is positive
        cashflows.append({
            "Instrument_ID": instrument_id,
            "Cashflow_Date": maturity_date,
            "Cashflow_Amount": amount if is_asset else -amount, # Positive for asset repayment, negative for liability repayment
            "Type": "Principal Maturity"
        })

    return pd.DataFrame(cashflows)


@st.cache_data
def apply_behavioral_assumptions(cashflow_df, instrument_data, prepayment_rate_annual, nmd_beta, nmd_behavioral_maturity_years):
    if cashflow_df.empty: return cashflow_df
    
    modified_cashflow_df = cashflow_df.copy()
    
    instrument_type = instrument_data["Instrument_Type"]
    specific_features = instrument_data["Specific_Features"]

    # Mortgage Prepayment
    if instrument_type == "Mortgage" and specific_features.get("prepayment_option"):
        # Find the original principal maturity cashflow
        principal_maturity_cf_idx = modified_cashflow_df[modified_cashflow_df["Type"] == "Principal Maturity"].index
        
        if not principal_maturity_cf_idx.empty:
            original_principal_idx = principal_maturity_cf_idx[0]
            original_principal_amount = modified_cashflow_df.loc[original_principal_idx, "Cashflow_Amount"]
            maturity_date = modified_cashflow_df.loc[original_principal_idx, "Cashflow_Date"]
            
            # Simplified prepayment logic: reduce final principal and add a prepayment cashflow earlier
            # Assuming prepayment reduces the final principal proportionally
            prepayment_amount_actual = abs(original_principal_amount) * prepayment_rate_annual
            
            # Reduce the final principal cashflow
            modified_cashflow_df.loc[original_principal_idx, "Cashflow_Amount"] -= np.sign(original_principal_amount) * prepayment_amount_actual
            
            # Add a prepayment cashflow. For simplicity, let's put it one year before maturity
            prepayment_date = maturity_date - relativedelta(years=1)
            # Ensure prepayment date is not before the issue date or initial cashflow date
            earliest_cf_date = modified_cashflow_df["Cashflow_Date"].min()
            if prepayment_date < earliest_cf_date:
                prepayment_date = earliest_cf_date + relativedelta(months=1) # Just after start

            new_prepayment_row = {
                "Instrument_ID": instrument_data["Instrument_ID"],
                "Cashflow_Date": prepayment_date,
                "Cashflow_Amount": np.sign(original_principal_amount) * prepayment_amount_actual, # Same sign as original principal
                "Type": "Prepayment"
            }
            modified_cashflow_df = pd.concat([modified_cashflow_df, pd.DataFrame([new_prepayment_row])], ignore_index=True)


    # Non-Maturity Deposit (NMD) Behavioral Maturity
    elif instrument_type == "Deposit" and specific_features.get("nmd_flag"):
        # For NMDs, the contractual maturity is usually very short (e.g., daily).
        # We model a behavioral maturity. The principal cashflow is shifted.
        
        # Find the original principal maturity cashflow (assuming one)
        principal_maturity_cf_idx = modified_cashflow_df[modified_cashflow_df["Type"] == "Principal Maturity"].index
        if not principal_maturity_cf_idx.empty:
            original_principal_idx = principal_maturity_cf_idx[0]
            
            # Calculate behavioral maturity date from valuation date (or an assumed start date)
            # The valuation date for the entire simulation is a good reference
            valuation_date_for_nmd = modified_cashflow_df["Cashflow_Date"].min() # Using the earliest cashflow date as proxy for start/valuation
            behavioral_maturity_date = valuation_date_for_nmd + relativedelta(years=nmd_behavioral_maturity_years)
            
            # Update the principal cashflow date to the behavioral maturity
            modified_cashflow_df.loc[original_principal_idx, "Cashflow_Date"] = behavioral_maturity_date
            
            # NMD Beta is applied during the PV calculation by adjusting the discount rate (or cashflow).
            # This function primarily handles the maturity shift.
            
    return modified_cashflow_df.sort_values(by="Cashflow_Date").reset_index(drop=True)


@st.cache_data
def map_cashflows_to_basel_buckets(cashflow_df, valuation_date, basel_bucket_definitions):
    if cashflow_df.empty: return pd.DataFrame()

    bucketed_data = []

    # Ensure valuation_date is a datetime object
    if isinstance(valuation_date, date) and not isinstance(valuation_date, datetime):
        valuation_date = datetime.combine(valuation_date, datetime.min.time())

    for _, row in cashflow_df.iterrows():
        cf_date = row["Cashflow_Date"]
        cf_amount = row["Cashflow_Amount"]

        # Only consider cashflows from valuation date onwards for gap analysis
        if cf_date < valuation_date:
            continue

        # Calculate months from valuation date to cashflow date
        time_delta_days = (cf_date - valuation_date).days
        months_to_cf = time_delta_days / 30.44 # Approximate months (average days in month)

        bucket_assigned = "20Y+" # Default for cashflows beyond 20 years
        for bucket_def in basel_bucket_definitions:
            min_m = bucket_def["min_months"]
            max_m = bucket_def["max_months"]

            if min_m <= months_to_cf < max_m:
                bucket_assigned = bucket_def["bucket"]
                break
        
        bucketed_data.append({
            "Instrument_ID": row["Instrument_ID"],
            "Cashflow_Date": cf_date,
            "Cashflow_Amount": cf_amount,
            "Bucket": bucket_assigned,
            "Is_Asset_Cashflow": cf_amount > 0 # Positive for assets (inflows), negative for liabilities (outflows)
        })

    return pd.DataFrame(bucketed_data)

@st.cache_data
def calculate_present_value_for_cashflows(cashflow_df, discount_curve, valuation_date, instrument_type=None, nmd_beta=0.0):
    if cashflow_df.empty: return 0.0

    total_pv = 0.0

    # Ensure valuation_date is a datetime object for comparison
    if isinstance(valuation_date, date) and not isinstance(valuation_date, datetime):\
        valuation_date = datetime.combine(valuation_date, datetime.min.time())

    # Create a mapping from Months_to_Maturity to Rate for quick lookup
    # Ensure discount_curve is sorted by Months_to_Maturity
    discount_curve = discount_curve.sort_values(by="Months_to_Maturity").reset_index(drop=True)
    
    # Interpolation function for rates
    interp_func = interp1d(
        discount_curve["Months_to_Maturity"],
        discount_curve["Rate"],
        kind="linear",
        fill_value="extrapolate" # Handle dates outside the explicit tenor range
    )

    for _, row in cashflow_df.iterrows():
        cf_date = row["Cashflow_Date"]
        cf_amount = row["Cashflow_Amount"]

        if cf_date < valuation_date:
            # Cashflows already occurred, not part of future PV (from valuation date onwards)
            continue

        # Calculate time in years from valuation date
        time_delta_days = (cf_date - valuation_date).days
        time_in_years = time_delta_days / 365.25 # More precise year calculation

        # Get the appropriate discount rate for this specific time_in_years
        months_to_cf = time_in_years * 12
        r_t = interp_func(months_to_cf).item()
        
        # Apply NMD Beta if it's an NMD liability
        if instrument_type == "Deposit" and row["Type"] in ["Interest", "Principal Maturity"] and cf_amount <= 0: # Check if it's a liability cashflow
            r_t = r_t * (1 - nmd_beta) # Reduce the effective discount rate for NMDs based on beta
                                        # This means NMD liabilities are less sensitive to rate changes

        # Avoid division by zero or problematic rates
        if (1 + r_t) <= 0:
            discount_factor = 0 # Prevent mathematical errors
        else:
            discount_factor = 1 / ((1 + r_t) ** time_in_years)

        total_pv += cf_amount * discount_factor

    return total_pv

@st.cache_data
def calculate_eve(pv_assets, pv_liabilities):
    return pv_assets - pv_liabilities

@st.cache_data
def calculate_net_gap(bucketed_cashflow_df):
    if bucketed_cashflow_df.empty: return pd.DataFrame()

    # Group by bucket and sum inflows (assets) and outflows (liabilities)
    # Inflows are positive cashflows, Outflows are negative cashflows (made positive for display)
    inflows_df = bucketed_cashflow_df[bucketed_cashflow_df["Is_Asset_Cashflow"]].groupby("Bucket")["Cashflow_Amount"].sum().rename("Total_Inflows")
    outflows_df = bucketed_cashflow_df[~bucketed_cashflow_df["Is_Asset_Cashflow"]].groupby("Bucket")["Cashflow_Amount"].sum().apply(lambda x: abs(x)).rename("Total_Outflows")

    net_gap_df = pd.concat([inflows_df, outflows_df], axis=1).fillna(0)

    # Calculate Net Gap (Inflows - Outflows)
    net_gap_df["Net_Gap"] = net_gap_df["Total_Inflows"] - net_gap_df["Total_Outflows"]

    # Ensure all Basel buckets are present and in order
    all_buckets_ordered = [b["bucket"] for b in basel_bucket_definitions_list]
    net_gap_df = net_gap_df.reindex(all_buckets_ordered, fill_value=0)

    return net_gap_df.reset_index().rename(columns={"index": "Bucket"})

@st.cache_data
def generate_basel_shocked_curve(baseline_curve, scenario_type, shock_magnitudes):
    shocked_curve = baseline_curve.copy()
    
    # Convert bps to decimal
    shock_magnitude_short = shock_magnitudes["short"] / 10000.0
    shock_magnitude_long = shock_magnitudes["long"] / 10000.0

    # Basel often defines short-term as <= 1 year (12 months), long-term as > 1 year
    short_term_threshold_months = 12 

    # Apply shock based on scenario type
    if scenario_type in ["Parallel Up", "Parallel Down"]:
        shocked_curve["Rate"] = baseline_curve["Rate"] + shock_magnitude_short # Same shock for all tenors
    elif scenario_type == "Steepener":
        # Short rates down, long rates up
        # The prompt examples for Steepener/Flattener shock magnitudes are confusing (e.g., short: -50, long: 100).
        # Typically, a steepener means the curve becomes steeper, e.g., short end goes down, long end goes up.
        # Let's interpret shock_magnitude_short as the shock for short-term, and shock_magnitude_long for long-term.
        shocked_curve["Rate"] = baseline_curve.apply(
            lambda row: row["Rate"] + (shock_magnitude_long if row["Months_to_Maturity"] > short_term_threshold_months else shock_magnitude_short),
            axis=1
        )
    elif scenario_type == "Flattener":
        # Short rates up, long rates down
        shocked_curve["Rate"] = baseline_curve.apply(
            lambda row: row["Rate"] + (shock_magnitude_short if row["Months_to_Maturity"] <= short_term_threshold_months else shock_magnitude_long),
            axis=1
        )
    elif scenario_type == "Short Rate Up":
        shocked_curve["Rate"] = baseline_curve.apply(
            lambda row: row["Rate"] + shock_magnitude_short if row["Months_to_Maturity"] <= short_term_threshold_months else row["Rate"],
            axis=1
        )
    elif scenario_type == "Short Rate Down":
        shocked_curve["Rate"] = baseline_curve.apply(
            lambda row: row["Rate"] + shock_magnitude_short if row["Months_to_Maturity"] <= short_term_threshold_months else row["Rate"],
            axis=1
        )
    else:
        # No shock or invalid scenario, return baseline
        pass

    # Ensure rates do not go negative (can cause issues with PV calculations)
    shocked_curve["Rate"] = shocked_curve["Rate"].clip(lower=0.0001) # Small positive floor

    return shocked_curve


@st.cache_data
def reprice_floating_instrument_cashflows_under_shock(instrument_cashflow_df, instrument_data, shocked_date_curve):
    if instrument_cashflow_df.empty: return instrument_cashflow_df

    repriced_cashflows = instrument_cashflow_df.copy()
    rate_type = instrument_data["Rate_Type"]
    amount = instrument_data["Amount"]
    payment_frequency = instrument_data["Payment_Frequency"]

    # Determine payment frequency in months
    if payment_frequency == "Monthly":
        freq_months = 1
    elif payment_frequency == "Quarterly":
        freq_months = 3
    elif payment_frequency == "Semi-Annually":
        freq_months = 6
    elif payment_frequency == "Annually":
        freq_months = 12
    else:
        freq_months = 12

    # Floating and Hybrid (e.g., Swaps with floating leg) instruments need repricing
    if rate_type == "Floating" or (rate_type == "Hybrid" and instrument_data["Instrument_Type"] == "Swap"):
        # Create an interpolation function for the shocked curve
        shocked_date_curve_sorted = shocked_date_curve.sort_values(by="Months_to_Maturity").reset_index(drop=True)
        interp_func = interp1d(
            shocked_date_curve_sorted["Months_to_Maturity"],
            shocked_date_curve_sorted["Rate"],
            kind="linear",
            fill_value="extrapolate"
        )
        
        valuation_date_for_reprice = shocked_date_curve_sorted["Valuation_Date"].iloc[0]

        for idx, row in repriced_cashflows.iterrows():
            if row["Type"] == "Interest":
                cf_date = row["Cashflow_Date"]
                
                # Calculate months from valuation date to the cashflow date
                time_delta_days = (cf_date - valuation_date_for_reprice).days
                months_to_cf = round(time_delta_days / 30.44)
                months_to_cf = max(0, months_to_cf)

                current_shocked_rate = interp_func(months_to_cf).item()
                
                # Adjust for specific features like floating spread if applicable (e.g., for swaps)
                floating_spread = instrument_data["Specific_Features"].get("floating_spread", 0.0)
                adjusted_rate = current_shocked_rate + floating_spread

                # Recalculate interest payment based on the new (shocked) rate
                new_interest_payment = amount * adjusted_rate * (freq_months / 12)
                
                # The sign depends on whether it's an asset or liability and if it's an inflow/outflow
                # For interest, if is_asset, it's an inflow (+), if not, it's an outflow (-)
                repriced_cashflows.loc[idx, "Cashflow_Amount"] = new_interest_payment if instrument_data["Is_Asset"] else -new_interest_payment

    return repriced_cashflows

@st.cache_data
def adjust_behavioral_assumptions_for_shock(cashflow_df, instrument_data, scenario_type, baseline_prepayment_rate, behavioral_shock_adjustment_factor):
    modified_cashflow_df = cashflow_df.copy()

    instrument_type = instrument_data["Instrument_Type"]
    specific_features = instrument_data["Specific_Features"]

    if instrument_type == "Mortgage" and specific_features.get("prepayment_option"):
        # Adjust prepayment rate under shock scenarios
        adjusted_prepayment_rate = baseline_prepayment_rate
        
        # Example logic: prepayment increases with rate cuts (Parallel Down, Short Rate Down)
        # and decreases with rate hikes (Parallel Up, Short Rate Up)
        if "Down" in scenario_type:
            adjusted_prepayment_rate = min(baseline_prepayment_rate * (1 + behavioral_shock_adjustment_factor), 1.0) # Cap at 100%
        elif "Up" in scenario_type:
            adjusted_prepayment_rate = max(baseline_prepayment_rate * (1 - behavioral_shock_adjustment_factor), 0.0) # Floor at 0%
            
        # If there are existing "Prepayment" cashflows, adjust their magnitude
        prepayment_rows = modified_cashflow_df[modified_cashflow_df["Type"] == "Prepayment"].index
        if not prepayment_rows.empty:
            # This is a very simplistic adjustment. Ideally, you'd re-run the full
            # behavioral model with the adjusted prepayment rate, which would
            # involve recalculating the distribution of principal over time.
            # For demonstration, we'll proportionally adjust the existing prepayment cashflow.
            if baseline_prepayment_rate > 0:
                scaling_factor = adjusted_prepayment_rate / baseline_prepayment_rate
                for idx in prepayment_rows:
                    modified_cashflow_df.loc[idx, "Cashflow_Amount"] *= scaling_factor
            elif baseline_prepayment_rate == 0 and adjusted_prepayment_rate > 0:
                # If baseline was 0 and now it's >0, this is more complex. It would mean adding new Cfs.
                # For this demo, we\'ll skip creation of new Cfs in this shock adjustment.
                pass


    # NMD behavioral maturity and beta are typically applied when calculating PV of NMD cashflows,
    # rather than modifying the cashflows themselves for behavioral maturity shifts under shock.
    # The `calculate_present_value_for_cashflows` already includes `nmd_beta`.

    return modified_cashflow_df


@st.cache_data
def recalculate_cashflows_and_pv_for_scenario(\
    portfolio_df,\
    shocked_curve_date_based,\
    valuation_date,\
    scenario_type,\
    baseline_prepayment_rate, # Needed for behavioral adjustment\n    behavioral_shock_adjustment_factor, # Needed for behavioral adjustment\n    nmd_beta,\
    nmd_behavioral_maturity_years\
):\
    all_shocked_cashflows = []\
    for index, instrument_data in portfolio_df.iterrows():\
        # 1. Generate baseline cashflows for the instrument\
        # For floating instruments, `calculate_cashflows_for_instrument` already uses the curve\
        # so if we pass the shocked curve here, it will generate initial cashflows based on shocked rates.\
        # This simplifies the floating rate re-pricing.\
        instrument_cfs = calculate_cashflows_for_instrument(\
            instrument_data, shocked_curve_date_based \
        )\
\
        # 2. Apply behavioral assumptions (e.g., NMD behavioral maturity, baseline prepayment)\
        instrument_cfs_after_behavioral = apply_behavioral_assumptions(\
            instrument_cfs,
            instrument_data,\
            prepayment_rate_annual=baseline_prepayment_rate,\n            nmd_beta=nmd_beta,\
            nmd_behavioral_maturity_years=nmd_behavioral_maturity_years\
        )\
\
        # 3. Apply behavioral adjustments specific to the shock scenario (e.g., changes in prepayment behavior)\
        instrument_cfs_final = adjust_behavioral_assumptions_for_shock(\
            instrument_cfs_after_behavioral,\
            instrument_data,\
            scenario_type,\
            baseline_prepayment_rate,\
            behavioral_shock_adjustment_factor\
        )\
\
        all_shocked_cashflows.append(instrument_cfs_final)\
\
    # Concatenate all instrument cashflows for the scenario\
    if not all_shocked_cashflows: return 0.0, 0.0, 0.0 \
    total_shocked_cashflows_df = pd.concat(all_shocked_cashflows, ignore_index=True)\
\
    # Separate assets and liabilities for PV calculation\
    assets_cfs = total_shocked_cashflows_df[total_shocked_cashflows_df["Cashflow_Amount"] > 0]\
    liabilities_cfs = total_shocked_cashflows_df[total_shocked_cashflows_df["Cashflow_Amount"] <= 0]\
\
    pv_assets_shocked = calculate_present_value_for_cashflows(assets_cfs, shocked_curve_date_based, valuation_date)\
    pv_liabilities_shocked = calculate_present_value_for_cashflows(liabilities_cfs, shocked_curve_date_based, valuation_date, instrument_type="Deposit", nmd_beta=nmd_beta)\
\
    eve_shocked = calculate_eve(pv_assets_shocked, pv_liabilities_shocked)\
\
    return eve_shocked, pv_assets_shocked, pv_liabilities_shocked


@st.cache_data
def calculate_delta_eve(baseline_eve, shocked_eve):
    return shocked_eve - baseline_eve

@st.cache_data
def report_delta_eve_as_percentage_of_tier1(delta_eve_results, tier1_capital):
    report = {}
    for scenario, delta_eve_val in delta_eve_results.items():
        if tier1_capital != 0:
            percentage = (delta_eve_val / tier1_capital) * 100
        else:
            percentage = 0.0 # Handle division by zero
        report[scenario] = percentage
    return report

