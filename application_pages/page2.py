
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import uuid
from scipy.interpolate import interp1d
import plotly.graph_objects as go
import plotly.express as px
import random

# --- Constants ---
PRODUCT_TYPES = ["Mortgage", "Corporate Loan", "Government Bond", "Non-Maturity Deposit", "Fixed Deposit", "Interest Rate Swap"]
ASSET_LIAB_TYPE = {"Mortgage": "Asset", "Corporate Loan": "Asset", "Government Bond": "Asset",
                   "Non-Maturity Deposit": "Liability", "Fixed Deposit": "Liability", "Interest Rate Swap": "Off-Balance Sheet"}
CURRENCIES = ["TWD", "USD"]
TENORS = ["3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "15Y", "20Y", "30Y"]
FIX_FLOAT_TYPES = ["Fixed", "Floating"]
RESET_FREQUENCIES = ["3M", "6M", "1Y"] # For floating instruments
PAYMENT_FREQUENCIES = ["Monthly", "Quarterly", "Semi-Annually", "Annually"]
RATE_BASIS_OPTIONS = ["Actual/360", "Actual/365", "30/360"]

market_rates_data = {
    "Tenor_Months": [1, 3, 6, 12, 24, 36, 60, 84, 120, 180, 240, 360],
    "Rate": [0.015, 0.017, 0.019, 0.022, 0.025, 0.028, 0.030, 0.032, 0.035, 0.037, 0.039, 0.040]
}
standard_tenors_months = [1, 3, 6, 12, 24, 36, 60, 84, 120, 180, 240, 360]

basel_bucket_definitions_list = [
    {"bucket": "0-1M", "min_days": 0, "max_days": 30},
    {"bucket": "1M-3M", "min_days": 31, "max_days": 90},
    {"bucket": "3M-6M", "min_days": 91, "max_days": 180},
    {"bucket": "6M-1Y", "min_days": 181, "max_days": 365},
    {"bucket": "1Y-2Y", "min_days": 366, "max_days": 730},
    {"bucket": "2Y-3Y", "min_days": 731, "max_days": 1095},
    {"bucket": "3Y-4Y", "min_days": 1096, "max_days": 1460},
    {"bucket": "4Y-5Y", "min_days": 1461, "max_days": 1825},
    {"bucket": "5Y-7Y", "min_days": 1826, "max_days": 2555},
    {"bucket": "7Y-10Y", "min_days": 2556, "max_days": 3650},
    {"bucket": "10Y-15Y", "min_days": 3651, "max_days": 5475},
    {"bucket": "15Y-20Y", "min_days": 5476, "max_days": 7300},
    {"bucket": "GT 20Y", "min_days": 7301, "max_days": np.inf}
]

shock_scenarios = {
    "Parallel Up": {"short_shock_bps": 100, "long_shock_bps": 100},
    "Parallel Down": {"short_shock_bps": -100, "long_shock_bps": -100},
    "Steepener": {"short_shock_bps": -150, "long_shock_bps": 100},
    "Flattener": {"short_shock_bps": 150, "long_shock_bps": -100},
    "Short-Up": {"short_shock_bps": 200, "long_shock_bps": 0},
    "Short-Down": {"short_shock_bps": -200, "long_shock_bps": 0},
}

# --- Core IRRBB Engine Functions ---

@st.cache_data(show_spinner=False)
def generate_synthetic_portfolio(num_instruments, tier1_capital, start_date, end_date):
    portfolio_data = []
    for _ in range(num_instruments):
        instrument_id = str(uuid.uuid4())
        product_type = random.choice(PRODUCT_TYPES)
        asset_liab_type = ASSET_LIAB_TYPE[product_type]
        currency = "TWD" # Simplified for this lab
        original_notional = round(random.uniform(5_000_000, 500_000_000), 2)
        issue_date = start_date + timedelta(days=random.randint(0, (end_date - start_date).days // 2))
        maturity_date = issue_date + relativedelta(months=random.choice([3, 6, 12, 24, 36, 60, 84, 120, 180, 240, 360]))

        if product_type == "Non-Maturity Deposit":
            maturity_date = None # NMDs don't have a contractual maturity

        coupon_rate = round(random.uniform(0.01, 0.05), 4)
        fix_float = random.choice(FIX_FLOAT_TYPES)
        reset_frequency = random.choice(RESET_FREQUENCIES) if fix_float == "Floating" else None
        payment_frequency = random.choice(PAYMENT_FREQUENCIES)
        rate_basis = random.choice(RATE_BASIS_OPTIONS)

        portfolio_data.append({
            "Instrument_ID": instrument_id,
            "Product_Type": product_type,
            "Asset_Liab_Type": asset_liab_type,
            "Currency": currency,
            "Original_Notional": original_notional,
            "Issue_Date": issue_date.strftime("%Y-%m-%d"),
            "Maturity_Date": maturity_date.strftime("%Y-%m-%d") if maturity_date else None,
            "Coupon_Rate": coupon_rate,
            "Fix_Float": fix_float,
            "Reset_Frequency": reset_frequency,
            "Payment_Frequency": payment_frequency,
            "Rate_Basis": rate_basis,
        })
    df = pd.DataFrame(portfolio_data)
    df["Issue_Date"] = pd.to_datetime(df["Issue_Date"])
    df["Maturity_Date"] = pd.to_datetime(df["Maturity_Date"])
    return df

@st.cache_data(show_spinner=False)
def create_baseline_discount_curve(valuation_date, market_rates, tenors_in_months, liquidity_spread_bps):
    market_rates_df = pd.DataFrame(market_rates)
    rates_interp_func = interp1d(market_rates_df["Tenor_Months"], market_rates_df["Rate"], kind="cubic", fill_value="extrapolate")
    
    discount_curve_data = []
    for tenor_m in tenors_in_months:
        interp_rate = rates_interp_func(tenor_m)
        adjusted_rate = interp_rate + (liquidity_spread_bps / 10000)
        discount_curve_data.append({"Tenor_Months": tenor_m, "Rate": adjusted_rate})
    return pd.DataFrame(discount_curve_data)

@st.cache_data(show_spinner=False)
def convert_tenor_curve_to_date_curve(tenor_curve_df, valuation_date_for_conversion):
    date_curve_data = []
    for _, row in tenor_curve_df.iterrows():
        tenor_months = row["Tenor_Months"]
        rate = row["Rate"]
        future_date = valuation_date_for_conversion + relativedelta(months=int(tenor_months))
        date_curve_data.append({"Date": future_date, "Rate": rate})
    return pd.DataFrame(date_curve_data)

@st.cache_data(show_spinner=False)
def calculate_cashflows_for_instrument(instrument_data, baseline_curve):
    product_type = instrument_data["Product_Type"]
    original_notional = instrument_data["Original_Notional"]
    issue_date = instrument_data["Issue_Date"]
    maturity_date = instrument_data["Maturity_Date"]
    coupon_rate = instrument_data["Coupon_Rate"]
    fix_float = instrument_data["Fix_Float"]
    payment_frequency = instrument_data["Payment_Frequency"]
    
    cashflows = []
    
    freq_map = {"Monthly": 1, "Quarterly": 3, "Semi-Annually": 6, "Annually": 12}
    payment_months = freq_map.get(payment_frequency, 12)

    if product_type == "Non-Maturity Deposit":
        # For NMDs, assume a single cashflow at valuation date for the notional for simplicity
        cashflows.append({
            "Instrument_ID": instrument_data["Instrument_ID"],
            "Date": datetime.today().date(), # NMD assumed active today
            "Cashflow_Amount": -original_notional, # Outflow for liability
            "Type": "Notional",
            "Asset_Liab_Type": instrument_data["Asset_Liab_Type"],
            "Fix_Float": fix_float,
            "Coupon_Rate": coupon_rate,
            "Product_Type": product_type
        })
        return pd.DataFrame(cashflows)
    
    if maturity_date is None:
        return pd.DataFrame() # Should be handled by NMD check

    current_date = issue_date
    while current_date <= maturity_date:
        # Ensure we only process future cashflows from valuation date or apply logic for past
        # For simplicity, cashflows are generated from issue date to maturity date.
        # PV calculation will handle which ones are relevant.

        # Interest payment
        interest_amount = original_notional * coupon_rate * (payment_months / 12)
        if current_date > issue_date or (current_date == issue_date and issue_date == datetime.today().date()): # Include initial payment if on valuation date
            cashflows.append({
                "Instrument_ID": instrument_data["Instrument_ID"],
                "Date": current_date,
                "Cashflow_Amount": interest_amount if instrument_data["Asset_Liab_Type"] == "Asset" else -interest_amount,
                "Type": "Interest",
                "Asset_Liab_Type": instrument_data["Asset_Liab_Type"],
                "Fix_Float": fix_float,
                "Coupon_Rate": coupon_rate,
                "Product_Type": product_type
            })

        # Principal payment at maturity
        if current_date == maturity_date:
            cashflows.append({
                "Instrument_ID": instrument_data["Instrument_ID"],
                "Date": current_date,
                "Cashflow_Amount": original_notional if instrument_data["Asset_Liab_Type"] == "Asset" else -original_notional,
                "Type": "Principal",
                "Asset_Liab_Type": instrument_data["Asset_Liab_Type"],
                "Fix_Float": fix_float,
                "Coupon_Rate": coupon_rate,
                "Product_Type": product_type
            })

        current_date += relativedelta(months=payment_months)

    df = pd.DataFrame(cashflows)
    df["Date"] = pd.to_datetime(df["Date"])
    return df

@st.cache_data(show_spinner=False)
def apply_behavioral_assumptions(cashflow_df, behavioral_flag, prepayment_rate_annual, nmd_beta, nmd_behavioral_maturity_years):
    if cashflow_df.empty:
        return cashflow_df

    modified_cashflow_df = cashflow_df.copy()

    if behavioral_flag == "Mortgage":
        # Simple prepayment: reduce all future cashflows by an annual prepayment factor
        # This is a highly simplified model for demonstration.
        # A more realistic model would apply prepayment to outstanding principal.
        if "Mortgage" in modified_cashflow_df["Product_Type"].unique():
            # For simplicity, a flat reduction factor on all future cashflows for mortgages
            # This is not how prepayments are calculated in real models but serves for concept.
            prepayment_factor = 1 - (prepayment_rate_annual / 12) # Monthly reduction from annual rate
            # Assuming `Cashflow_Amount` here includes both principal and interest for simplification
            # Only apply to future cashflows (after current date)
            today = datetime.today().date() # Or valuation_date if passed
            modified_cashflow_df.loc[(modified_cashflow_df["Product_Type"] == "Mortgage") & 
                                     (modified_cashflow_df["Date"] > today), "Cashflow_Amount"] *= prepayment_factor

    if behavioral_flag == "NMD":
        nmd_instrument_ids = modified_cashflow_df[modified_cashflow_df["Product_Type"] == "Non-Maturity Deposit"]["Instrument_ID"].unique()
        for inst_id in nmd_instrument_ids:
            # Remove existing cashflows for this NMD instrument if any were generated (e.g., initial notional)
            modified_cashflow_df = modified_cashflow_df[~((modified_cashflow_df["Instrument_ID"] == inst_id) & 
                                                          (modified_cashflow_df["Product_Type"] == "Non-Maturity Deposit"))]
            
            # Create new behavioral cashflows for NMD
            notional = cashflow_df[cashflow_df["Instrument_ID"] == inst_id]["Cashflow_Amount"].abs().max() # Get original notional
            if pd.isna(notional) or notional == 0: continue

            # Distribute notional over behavioral maturity with interest based on NMD beta
            num_months = int(nmd_behavioral_maturity_years * 12)
            if num_months == 0: num_months = 1 # Avoid division by zero

            # Simple amortization for behavioral NMD
            monthly_principal_payment = notional / num_months
            remaining_notional = notional
            current_date = datetime.today().date() # Start NMD behavioral cashflows from today

            for i in range(num_months):
                payment_date = current_date + relativedelta(months=i+1)
                # NMD interest is typically linked to a benchmark (e.g., policy rate) * NMD beta
                # For simplicity, assume a fixed "effective rate" for the NMD for now based on beta.
                # In a real model, this rate would be dynamic based on market rates.
                behavioral_interest = remaining_notional * nmd_beta * (1 / 12) # Monthly interest
                
                modified_cashflow_df = pd.concat([modified_cashflow_df, pd.DataFrame([{
                    "Instrument_ID": inst_id,
                    "Date": payment_date,
                    "Cashflow_Amount": -behavioral_interest, # NMD interest is an outflow
                    "Type": "Behavioral Interest",
                    "Asset_Liab_Type": "Liability",
                    "Fix_Float": "Floating", # NMDs are floating-like
                    "Coupon_Rate": nmd_beta,
                    "Product_Type": "Non-Maturity Deposit"
                }])], ignore_index=True)
                
                if i == num_months - 1: # Last payment includes remaining principal
                    principal_payment = remaining_notional
                else:
                    principal_payment = monthly_principal_payment
                
                modified_cashflow_df = pd.concat([modified_cashflow_df, pd.DataFrame([{
                    "Instrument_ID": inst_id,
                    "Date": payment_date,
                    "Cashflow_Amount": -principal_payment, # NMD principal is an outflow
                    "Type": "Behavioral Principal",
                    "Asset_Liab_Type": "Liability",
                    "Fix_Float": "Floating",
                    "Coupon_Rate": nmd_beta,
                    "Product_Type": "Non-Maturity Deposit"
                }])], ignore_index=True)
                remaining_notional -= principal_payment

    return modified_cashflow_df.sort_values(by="Date").reset_index(drop=True)

@st.cache_data(show_spinner=False)
def map_cashflows_to_basel_buckets(cashflow_df, valuation_date, basel_bucket_definitions):
    if cashflow_df.empty:
        return pd.DataFrame()

    bucketed_data = []
    
    # Sort cashflows by date to process chronologically
    cashflow_df_sorted = cashflow_df.sort_values(by="Date").copy()

    for _, row in cashflow_df_sorted.iterrows():
        cf_date = row["Date"]
        days_to_maturity = (cf_date - valuation_date).days
        
        bucket_found = False
        for bucket_def in basel_bucket_definitions:
            if bucket_def["min_days"] <= days_to_maturity <= bucket_def["max_days"]:
                bucketed_data.append({
                    "Instrument_ID": row["Instrument_ID"],
                    "Date": row["Date"],
                    "Cashflow_Amount": row["Cashflow_Amount"],
                    "Type": row["Type"],
                    "Asset_Liab_Type": row["Asset_Liab_Type"],
                    "Bucket": bucket_def["bucket"],
                    "Fix_Float": row["Fix_Float"],
                    "Coupon_Rate": row["Coupon_Rate"],
                    "Product_Type": row["Product_Type"]
                })
                bucket_found = True
                break
        # If a cashflow date is before valuation date, or falls outside defined buckets, handle as "Past" or "Uncategorized"
        if not bucket_found and days_to_maturity >= 0: # Only consider future or today for buckets
             # If it's greater than max of last bucket, put in last bucket
            if days_to_maturity > basel_bucket_definitions[-1]["max_days"]:
                last_bucket = basel_bucket_definitions[-1]["bucket"]
                bucketed_data.append({
                    "Instrument_ID": row["Instrument_ID"],
                    "Date": row["Date"],
                    "Cashflow_Amount": row["Cashflow_Amount"],
                    "Type": row["Type"],
                    "Asset_Liab_Type": row["Asset_Liab_Type"],
                    "Bucket": last_bucket,
                    "Fix_Float": row["Fix_Float"],
                    "Coupon_Rate": row["Coupon_Rate"],
                    "Product_Type": row["Product_Type"]
                })

    df = pd.DataFrame(bucketed_data)
    if not df.empty:
        # Ensure bucket order for consistency
        df["Bucket"] = pd.Categorical(df["Bucket"], categories=[b["bucket"] for b in basel_bucket_definitions], ordered=True)
        df = df.sort_values("Bucket")
    return df

@st.cache_data(show_spinner=False)
def calculate_present_value_for_cashflows(cashflow_df, discount_curve, valuation_date):
    if cashflow_df.empty:
        return 0.0, pd.DataFrame() # Return PV, and PV breakdown

    total_pv = 0.0
    pv_data = []

    # Ensure discount_curve has 'Date' as datetime and is sorted
    discount_curve["Date"] = pd.to_datetime(discount_curve["Date"])
    discount_curve = discount_curve.sort_values(by="Date")

    if discount_curve.shape[0] < 2:
        st.warning("Discount curve has too few points for interpolation. PV may be inaccurate or zero.")
        # If only one point, use that rate for everything, or return 0
        if discount_curve.shape[0] == 1:
            fixed_rate = discount_curve["Rate"].iloc[0]
            for _, row in cashflow_df.iterrows():
                cf_date = row["Date"]
                cashflow_amount = row["Cashflow_Amount"]
                days_from_valuation = (cf_date - valuation_date).days
                if days_from_valuation < 0: continue
                t_years = days_from_valuation / 365.25
                pv_cf = cashflow_amount / ((1 + fixed_rate)**t_years) if t_years > 0 else cashflow_amount
                total_pv += pv_cf
                pv_data.append({
                    "Instrument_ID": row["Instrument_ID"], "Date": row["Date"],
                    "Cashflow_Amount": row["Cashflow_Amount"], "Present_Value": pv_cf,
                    "Asset_Liab_Type": row["Asset_Liab_Type"]
                })
            return total_pv, pd.DataFrame(pv_data)
        else: # Empty discount curve
            return 0.0, pd.DataFrame()

    discount_curve["Days_From_Valuation"] = (discount_curve["Date"] - valuation_date).dt.days
    discount_curve_future = discount_curve[discount_curve["Days_From_Valuation"] >= 0].copy()
    
    if discount_curve_future.empty:
        st.warning("No future rates in discount curve relative to valuation date. PV will be zero.")
        return 0.0, pd.DataFrame()
    
    # Ensure unique days for interpolation, take mean rate if duplicates at same day-from-valuation
    discount_curve_future = discount_curve_future.groupby("Days_From_Valuation")["Rate"].mean().reset_index()

    rate_interp_func = interp1d(discount_curve_future["Days_From_Valuation"], discount_curve_future["Rate"], 
                                kind="linear", fill_value="extrapolate")

    for _, row in cashflow_df.iterrows():
        cf_date = row["Date"]
        cashflow_amount = row["Cashflow_Amount"]

        days_from_valuation = (cf_date - valuation_date).days
        
        if days_from_valuation < 0: # Cash flow is in the past
            pv_cf = 0.0
            continue 
        elif days_from_valuation == 0: # Cash flow on valuation date
            pv_cf = cashflow_amount
        else:
            try:
                t_years = days_from_valuation / 365.25 # Use 365.25 for average days in a year
                discount_rate_annual = rate_interp_func(days_from_valuation).item()

                if (1 + discount_rate_annual) <= 0: # Handle non-positive base for power
                    # This can happen with very negative rates, or rates around -100%
                    st.warning(f"Discount rate {discount_rate_annual:.4f} leads to non-positive (1+r) for CF on {cf_date}. Skipping PV for this CF.")
                    pv_cf = 0.0
                else:
                    pv_cf = cashflow_amount / ((1 + discount_rate_annual)**t_years)
            except Exception as e:
                st.error(f"Error calculating PV for CF on {cf_date} with days {days_from_valuation}: {e}")
                pv_cf = 0.0 # Default to 0 on error
        
        total_pv += pv_cf
        pv_data.append({
            "Instrument_ID": row["Instrument_ID"],
            "Date": row["Date"],
            "Cashflow_Amount": row["Cashflow_Amount"],
            "Present_Value": pv_cf,
            "Asset_Liab_Type": row["Asset_Liab_Type"]
        })
    
    return total_pv, pd.DataFrame(pv_data)


@st.cache_data(show_spinner=False)
def calculate_eve(pv_assets, pv_liabilities):
    return pv_assets + pv_liabilities # Liabilities are typically negative PV

@st.cache_data(show_spinner=False)
def calculate_net_gap(bucketed_cashflow_df):
    if bucketed_cashflow_df.empty:
        return pd.DataFrame(columns=["Bucket", "Total_Inflows", "Total_Outflows", "Net_Gap"])

    net_gap_data = []
    unique_buckets_order = [b["bucket"] for b in basel_bucket_definitions_list]
    
    for bucket in unique_buckets_order:
        bucket_cfs = bucketed_cashflow_df[bucketed_cashflow_df["Bucket"] == bucket]
        
        inflows = bucket_cfs[bucket_cfs["Asset_Liab_Type"] == "Asset"]["Cashflow_Amount"].sum()
        outflows = abs(bucket_cfs[bucket_cfs["Asset_Liab_Type"] == "Liability"]["Cashflow_Amount"].sum()) # Outflows are negative, so abs

        net_gap = inflows - outflows
        net_gap_data.append({
            "Bucket": bucket,
            "Total_Inflows": inflows,
            "Total_Outflows": outflows,
            "Net_Gap": net_gap
        })
    df = pd.DataFrame(net_gap_data)
    df["Bucket"] = pd.Categorical(df["Bucket"], categories=unique_buckets_order, ordered=True)
    return df.sort_values("Bucket")

@st.cache_data(show_spinner=False)
def generate_basel_shocked_curve(baseline_curve_df, scenario_type, shock_magnitude_bps_short, shock_magnitude_bps_long):
    shocked_curve = baseline_curve_df.copy()
    
    shock_short_decimal = shock_magnitude_bps_short / 10000
    shock_long_decimal = shock_magnitude_bps_long / 10000

    short_tenor_threshold_months = 12 # 1 year
    long_tenor_threshold_months = 60  # 5 years

    if scenario_type in ["Parallel Up", "Parallel Down"]:
        shocked_curve["Rate"] = shocked_curve["Rate"] + shock_short_decimal # For parallel, short and long shocks are same
    elif scenario_type in ["Steepener", "Flattener"]:
        def apply_tenor_shock(row):
            tenor_m = row["Tenor_Months"]
            if tenor_m <= short_tenor_threshold_months:
                shock = shock_short_decimal
            elif tenor_m >= long_tenor_threshold_months:
                shock = shock_long_decimal
            else:
                # Interpolate shock between short and long tenors
                interp_factor = (tenor_m - short_tenor_threshold_months) / (long_tenor_threshold_months - short_tenor_threshold_months)
                shock = shock_short_decimal * (1 - interp_factor) + shock_long_decimal * interp_factor
            return row["Rate"] + shock
        shocked_curve["Rate"] = shocked_curve.apply(apply_tenor_shock, axis=1)
    elif scenario_type == "Short-Up" or scenario_type == "Short-Down":
        # Apply shock only to short end; long end remains unchanged (0 shock)
        shocked_curve.loc[shocked_curve["Tenor_Months"] <= short_tenor_threshold_months, "Rate"] += shock_short_decimal

    return shocked_curve


@st.cache_data(show_spinner=False)
def reprice_floating_instrument_cashflows_under_shock(instrument_cashflow_df, instrument_data, shocked_date_curve):
    if instrument_cashflow_df.empty or instrument_data["Fix_Float"] == "Fixed":
        return instrument_cashflow_df.copy()

    repriced_cashflows = instrument_cashflow_df.copy()
    
    shocked_date_curve["Date"] = pd.to_datetime(shocked_date_curve["Date"])
    shocked_date_curve = shocked_date_curve.sort_values(by="Date")

    if shocked_date_curve.empty or shocked_date_curve.shape[0] < 2:
        st.warning("Shocked discount curve has too few points for re-pricing interpolation.")
        return repriced_cashflows # Return original if cannot reprice

    # Create interpolation function for shocked rates based on date values
    shock_rate_interp_func = interp1d(shocked_date_curve["Date"].apply(lambda x: (x - shocked_date_curve["Date"].min()).days), 
                                      shocked_date_curve["Rate"], kind="linear", fill_value="extrapolate")

    # Iterate only over floating interest cashflows
    for idx, row in repriced_cashflows[
        (repriced_cashflows["Fix_Float"] == "Floating") & 
        (repriced_cashflows["Type"] == "Interest")
    ].iterrows():
        cf_date = row["Date"]
        old_coupon_rate = row["Coupon_Rate"]

        # Calculate days from the earliest date in the shocked curve to maintain consistent interpolation domain
        days_from_shock_curve_start = (cf_date - shocked_date_curve["Date"].min()).days
        
        # Get the shocked rate for this cashflow date
        shocked_coupon_rate = shock_rate_interp_func(days_from_shock_curve_start).item()

        if old_coupon_rate == 0:
            # If old rate was 0 and new rate is also 0, no change.
            # If old rate was 0 but new rate is not, it implies a new interest calculation.
            # This highly simplifies; assumes notional * (new_rate - old_rate) * period_factor
            # For this simple model, if old_coupon_rate was 0, and now it's non-zero, it's an issue of cashflow generation.
            # Let's assume floating instruments always start with some positive coupon for re-pricing.
            st.warning(f"Floating instrument {row['Instrument_ID']} had a zero coupon rate. Repricing might be inaccurate.")
            # If old rate was zero, and new is also zero, no change in cashflow
            if shocked_coupon_rate == 0: continue
            else: # If old rate was zero, but new rate is non-zero, this is a problematic case for ratio. 
                  # For simplicity, if we hit this, we won't reprice this CF component accurately. Skip.
                  pass
        else:
            # Adjust cashflow amount proportionally to the change in coupon rate
            repriced_cashflows.loc[idx, "Cashflow_Amount"] = row["Cashflow_Amount"] * (shocked_coupon_rate / old_coupon_rate)
            repriced_cashflows.loc[idx, "Coupon_Rate"] = shocked_coupon_rate # Update the rate itself

    return repriced_cashflows

@st.cache_data(show_spinner=False)
def adjust_behavioral_assumptions_for_shock(scenario_type, baseline_prepayment_rate, nmd_beta_val, behavioral_shock_adjustment_factor):
    # This function now calculates the *adjusted* behavioral rates for the shocked scenario
    adjusted_prepayment_rate = baseline_prepayment_rate
    adjusted_nmd_beta = nmd_beta_val

    if scenario_type in ["Parallel Up", "Short-Up", "Flattener"]: # Rates generally rising or long end falling (less incentive to prepay)
        adjusted_prepayment_rate = max(0, baseline_prepayment_rate * (1 - behavioral_shock_adjustment_factor))
        adjusted_nmd_beta = min(1.0, nmd_beta_val * (1 + behavioral_shock_adjustment_factor)) # More pass-through
    elif scenario_type in ["Parallel Down", "Short-Down", "Steepener"]: # Rates generally falling or long end rising (more incentive to prepay)
        adjusted_prepayment_rate = baseline_prepayment_rate * (1 + behavioral_shock_adjustment_factor)
        adjusted_nmd_beta = max(0.0, nmd_beta_val * (1 - behavioral_shock_adjustment_factor)) # Less pass-through
    
    return adjusted_prepayment_rate, adjusted_nmd_beta

@st.cache_data(show_spinner=False)
def recalculate_cashflows_and_pv_for_scenario(portfolio_df, shocked_date_curve, valuation_date, scenario_type,
                                               baseline_prepayment_rate, baseline_nmd_beta,
                                               nmd_behavioral_maturity_years, behavioral_shock_adjustment_factor):
    all_scenario_cash_flows = []
    
    # 1. Adjust behavioral assumptions for the shock based on scenario type
    adjusted_prepayment_rate, adjusted_nmd_beta = adjust_behavioral_assumptions_for_shock(
        scenario_type, baseline_prepayment_rate, baseline_nmd_beta, behavioral_shock_adjustment_factor
    )

    for _, instrument_data in portfolio_df.iterrows():
        # Start with original cashflows for the instrument, then reprice/apply behavioral for shock
        # Need to re-generate base cashflows based on original instrument data for each scenario
        # to apply behavioral / repricing on a fresh set for the scenario.
        # This might be computationally intensive, but ensures correctness based on scenario conditions.
        instrument_original_cfs = calculate_cashflows_for_instrument(instrument_data, shocked_date_curve) # Pass shocked curve, though fixed rates don't change
        
        # 2. Apply behavioral assumptions with *adjusted* rates to these cashflows
        product_type = instrument_data["Product_Type"]
        behavioral_flag = None
        if product_type == "Mortgage":
            behavioral_flag = "Mortgage"
        elif product_type == "Non-Maturity Deposit":
            behavioral_flag = "NMD"
            
        instrument_cashflows_behavioral = apply_behavioral_assumptions(
            instrument_original_cfs,
            behavioral_flag,
            adjusted_prepayment_rate, # Use adjusted prepayment
            adjusted_nmd_beta,        # Use adjusted NMD beta
            nmd_behavioral_maturity_years
        )
        
        # 3. Reprice floating instruments under the shocked curve
        instrument_cashflows_repriced = reprice_floating_instrument_cashflows_under_shock(
            instrument_cashflows_behavioral, instrument_data, shocked_date_curve
        )
        
        all_scenario_cash_flows.append(instrument_cashflows_repriced)

    if not all_scenario_cash_flows:
        return 0.0, pd.DataFrame() # No cash flows, no EVE

    combined_cash_flows_scenario = pd.concat(all_scenario_cash_flows).reset_index(drop=True)
    
    # Calculate PV for assets and liabilities separately using the shocked curve
    pv_assets_scenario, _ = calculate_present_value_for_cashflows(
        combined_cash_flows_scenario[combined_cash_flows_scenario["Asset_Liab_Type"] == "Asset"],
        shocked_date_curve,
        valuation_date
    )
    pv_liabilities_scenario, _ = calculate_present_value_for_cashflows(
        combined_cash_flows_scenario[combined_cash_flows_scenario["Asset_Liab_Type"] == "Liability"],
        shocked_date_curve,
        valuation_date
    )

    eve_shocked = calculate_eve(pv_assets_scenario, pv_liabilities_scenario)
    
    return eve_shocked, combined_cash_flows_scenario

@st.cache_data(show_spinner=False)
def calculate_delta_eve(baseline_eve, shocked_eve):
    return shocked_eve - baseline_eve

@st.cache_data(show_spinner=False)
def report_delta_eve_as_percentage_of_tier1(delta_eve_results, tier1_capital):
    report_data = []
    for scenario, delta_eve_val in delta_eve_results.items():
        percentage = (delta_eve_val / tier1_capital) * 100
        report_data.append({"Scenario": scenario, "Delta_EVE_Value": delta_eve_val, "Percentage_of_Tier1_Capital": percentage})
    return pd.DataFrame(report_data)

# --- Visualization Function (Plotly) ---
def plot_delta_eve_bar_chart(delta_eve_report_df):
    fig = px.bar(delta_eve_report_df, x="Scenario", y="Percentage_of_Tier1_Capital",
                 title="Delta EVE by Basel Interest Rate Shock Scenario (% of Tier 1 Capital)",
                 labels={"Percentage_of_Tier1_Capital": "Delta EVE (% of Tier 1 Capital)"},
                 color="Percentage_of_Tier1_Capital",
                 color_continuous_scale=px.colors.sequential.Viridis,
                 template="plotly_white")
    fig.update_layout(xaxis_title="Interest Rate Shock Scenario", yaxis_title="Delta EVE (% of Tier 1 Capital)")
    return fig


# --- Main page function for page2.py ---
def run_page2():
    st.header("IRRBB Economic Value of Equity (EVE) Simulation")

    st.sidebar.subheader("Portfolio Generation Parameters")
    num_instruments = st.sidebar.slider(
        "Number of Instruments", min_value=1, max_value=100, value=25, step=1,
        help="Number of synthetic financial instruments to generate for the portfolio."
    )
    tier1_capital_val = st.sidebar.number_input(
        "Tier 1 Capital (TWD)", min_value=100_000_000, max_value=10_000_000_000, value=1_000_000_000, step=100_000_000,
        help="Bank's Tier 1 Capital, used for Delta EVE percentage calculation."
    )
    start_date_gen = st.sidebar.date_input(
        "Portfolio Start Date", value=date(2023, 1, 1),
        help="Start date for generating instrument issue dates."
    )
    end_date_gen = st.sidebar.date_input(
        "Portfolio End Date", value=date(2050, 12, 31),
        help="End date for generating instrument maturity dates."
    )
    valuation_date = st.sidebar.date_input(
        "Valuation Date", value=datetime.today().date(),
        help="Date as of which all present value calculations are performed."
    )
    
    st.sidebar.subheader("Discount Curve Parameters")
    liquidity_spread_bps_val = st.sidebar.slider(
        "Liquidity Spread (bps)", min_value=0, max_value=100, value=10, step=1,
        help="An additional spread applied to the risk-free discount curve."
    )

    st.sidebar.subheader("Behavioral Assumption Parameters")
    prepayment_rate_annual_val = st.sidebar.slider(
        "Annual Mortgage Prepayment Rate", min_value=0.0, max_value=0.2, value=0.05, step=0.01, format="%.2f",
        help="Annual rate at which mortgages are expected to be prepaid."
    )
    nmd_beta_val = st.sidebar.slider(
        "NMD Beta", min_value=0.0, max_value=1.0, value=0.5, step=0.05, format="%.2f",
        help="Sensitivity of Non-Maturity Deposit rates to market interest rates (0-1)."
    )
    nmd_behavioral_maturity_years_val = st.sidebar.slider(
        "NMD Behavioral Maturity (Years)", min_value=1.0, max_value=10.0, value=3.0, step=0.5, format="%.1f",
        help="Assumed average life of Non-Maturity Deposits for behavioral modeling."
    )
    behavioral_shock_adjustment_factor = st.sidebar.slider(
        "Behavioral Shock Adjustment Factor", min_value=0.0, max_value=0.5, value=0.10, step=0.01, format="%.2f",
        help="Factor to adjust behavioral rates (e.g., prepayment) under interest rate shock scenarios."
    )
    
    st.sidebar.markdown("---") # Separator
    if st.sidebar.button("Run IRRBB Simulation"): # This button triggers all calculations and displays
        with st.spinner("Generating Portfolio and Running Simulation..."):
            # 1. Generate Portfolio
            taiwan_portfolio_df = generate_synthetic_portfolio(num_instruments, tier1_capital_val, start_date_gen, end_date_gen)
            st.session_state["taiwan_portfolio_df"] = taiwan_portfolio_df

            # 2. Create Baseline Discount Curve
            baseline_discount_curve_df = create_baseline_discount_curve(valuation_date, market_rates_data, standard_tenors_months, liquidity_spread_bps_val)
            baseline_date_curve_df = convert_tenor_curve_to_date_curve(baseline_discount_curve_df, valuation_date)
            st.session_state["baseline_discount_curve_df"] = baseline_discount_curve_df
            st.session_state["baseline_date_curve_df"] = baseline_date_curve_df

            # 3. Pre-processing and Cash Flow Generation (Baseline)
            all_cash_flows_baseline = []
            progress_bar_cf = st.progress(0)
            status_text_cf = st.empty()
            
            for i, instrument_data in taiwan_portfolio_df.iterrows():
                status_text_cf.text(f"Generating cash flows for instrument {i+1}/{len(taiwan_portfolio_df)}...")
                # Generate raw cashflows for the instrument
                instrument_cashflows = calculate_cashflows_for_instrument(instrument_data, baseline_date_curve_df)
                
                # Apply behavioral assumptions (prepayment, NMD) to the baseline cashflows
                product_type = instrument_data["Product_Type"]
                behavioral_flag = None
                if product_type == "Mortgage":
                    behavioral_flag = "Mortgage"
                elif product_type == "Non-Maturity Deposit":
                    behavioral_flag = "NMD"
                
                instrument_cashflows_behavioral = apply_behavioral_assumptions(
                    instrument_cashflows.assign(Product_Type=product_type), # Pass Product_Type for behavioral functions
                    behavioral_flag,
                    prepayment_rate_annual_val,
                    nmd_beta_val,
                    nmd_behavioral_maturity_years_val
                )
                all_cash_flows_baseline.append(instrument_cashflows_behavioral)
                progress_bar_cf.progress((i + 1) / len(taiwan_portfolio_df))
            
            if all_cash_flows_baseline:
                combined_cash_flows_baseline = pd.concat(all_cash_flows_baseline).reset_index(drop=True)
            else:
                combined_cash_flows_baseline = pd.DataFrame() # Handle empty case

            st.session_state["combined_cash_flows_baseline"] = combined_cash_flows_baseline
            progress_bar_cf.empty()
            status_text_cf.empty()

            # 4. Baseline EVE Calculation and Gap Analysis
            st.subheader("Calculating Baseline EVE and Net Gap...")
            pv_assets_baseline, _ = calculate_present_value_for_cashflows(
                combined_cash_flows_baseline[combined_cash_flows_baseline["Asset_Liab_Type"] == "Asset"],
                baseline_date_curve_df,
                valuation_date
            )
            pv_liabilities_baseline, _ = calculate_present_value_for_cashflows(
                combined_cash_flows_baseline[combined_cash_flows_baseline["Asset_Liab_Type"] == "Liability"],
                baseline_date_curve_df,
                valuation_date
            )
            baseline_eve = calculate_eve(pv_assets_baseline, pv_liabilities_baseline)
            st.session_state["baseline_eve"] = baseline_eve
            st.session_state["pv_assets_baseline"] = pv_assets_baseline
            st.session_state["pv_liabilities_baseline"] = pv_liabilities_baseline

            bucketted_cash_flows_df = map_cashflows_to_basel_buckets(combined_cash_flows_baseline, valuation_date, basel_bucket_definitions_list)
            net_gap_table_df = calculate_net_gap(bucketted_cash_flows_df)
            st.session_state["net_gap_table_df"] = net_gap_table_df

            # 5. Scenario Shock Application and Revaluation
            delta_eve_results = {}
            
            st.subheader("Running Stress Scenarios...")
            scenario_progress_bar = st.progress(0)
            scenario_status_text = st.empty()

            for i, (scenario_name, shock_params) in enumerate(shock_scenarios.items()):
                scenario_status_text.text(f"Calculating for scenario: {scenario_name}...")
                
                shocked_tenor_curve = generate_basel_shocked_curve(
                    baseline_discount_curve_df,
                    scenario_name,
                    shock_params["short_shock_bps"],
                    shock_params["long_shock_bps"]
                )
                shocked_date_curve = convert_tenor_curve_to_date_curve(shocked_tenor_curve, valuation_date)

                eve_shocked, _ = recalculate_cashflows_and_pv_for_scenario(
                    taiwan_portfolio_df, # Pass portfolio to re-generate cashflows under shock
                    shocked_date_curve,
                    valuation_date,
                    scenario_name,
                    prepayment_rate_annual_val,
                    nmd_beta_val,
                    nmd_behavioral_maturity_years_val,
                    behavioral_shock_adjustment_factor
                )
                delta_eve = calculate_delta_eve(baseline_eve, eve_shocked)
                delta_eve_results[scenario_name] = delta_eve
                scenario_progress_bar.progress((i + 1) / len(shock_scenarios))
            
            st.session_state["delta_eve_results"] = delta_eve_results
            scenario_progress_bar.empty()
            scenario_status_text.empty()

            # 6. Delta EVE Reporting
            delta_eve_report_df = report_delta_eve_as_percentage_of_tier1(delta_eve_results, tier1_capital_val)
            st.session_state["delta_eve_report_df"] = delta_eve_report_df

            st.success("Simulation complete!")

    # Display Results (only if simulation has been run and data is in session state)
    if "taiwan_portfolio_df" in st.session_state:
        st.subheader("1. Initial Portfolio Overview")
        st.dataframe(st.session_state["taiwan_portfolio_df"].head())
        with st.expander("View Full Portfolio Details"):
            st.dataframe(st.session_state["taiwan_portfolio_df"])

        st.subheader("2. Baseline Discount Curve")
        st.dataframe(st.session_state["baseline_discount_curve_df"])
        with st.expander("View Baseline Date Curve Details"):
            st.dataframe(st.session_state["baseline_date_curve_df"])

        st.subheader("3. Baseline Economic Value of Equity (EVE)")
        col1, col2, col3 = st.columns(3)
        col1.metric("Baseline EVE", f"{st.session_state['baseline_eve']:, .2f} TWD")
        col2.metric("PV of Assets (Baseline)", f"{st.session_state['pv_assets_baseline']:, .2f} TWD")
        col3.metric("PV of Liabilities (Baseline)", f"{st.session_state['pv_liabilities_baseline']:, .2f} TWD")
        
        st.subheader("4. Net Gap Analysis")
        st.table(st.session_state["net_gap_table_df"])
        
        if not st.session_state["net_gap_table_df"].empty:
            fig_gap = px.bar(st.session_state["net_gap_table_df"], x="Bucket", y="Net_Gap",
                             title="Net Gap by Basel Time Bucket",
                             labels={"Net_Gap": "Net Gap (TWD)"},
                             color="Net_Gap",
                             color_continuous_scale=px.colors.sequential.Bluered,
                             template="plotly_white")
            st.plotly_chart(fig_gap, use_container_width=True)


        st.subheader("5. Delta EVE Report (% of Tier 1 Capital)")
        st.table(st.session_state["delta_eve_report_df"])
        
        if not st.session_state["delta_eve_report_df"].empty:
            fig_delta_eve = plot_delta_eve_bar_chart(st.session_state["delta_eve_report_df"])
            st.plotly_chart(fig_delta_eve, use_container_width=True)

        st.markdown("""
        **Interpretation of $\Delta EVE$ Chart:**
        - A negative $\Delta EVE$ indicates a decrease in the bank's economic value under the specific interest rate shock scenario.
        - A positive $\Delta EVE$ indicates an increase in economic value.
        - Regulators typically focus on adverse scenarios (negative $\Delta EVE$) and require banks to manage risks to stay within limits relative to Tier 1 Capital.
        """)
