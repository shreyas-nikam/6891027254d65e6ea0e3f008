
# Streamlit Application Requirements Specification: IRRBB EVE Simulation

This document outlines the requirements for developing a Streamlit application based on the provided Jupyter Notebook and user requirements. It will serve as a blueprint for implementing the interactive IRRBB EVE simulation.

## 1. Application Overview

The Streamlit application will implement a full-revaluation Interest Rate Risk in the Banking Book (IRRBB) engine. It will allow users to generate a synthetic banking book portfolio, simulate cash flows, apply various Basel interest rate shock scenarios, and calculate the resulting change in Economic Value of Equity ($\Delta EVE$).

### Learning Goals

Upon using this application, users will be able to:
*   Assemble a banking-book positions dataset that captures interest-sensitive assets, liabilities, and (optionally) simple hedges.
*   Generate synthetic cash-flow data for those positions, respecting product features and behavioural assumptions.
*   Build a full-revaluation IRRBB engine that computes baseline present values, allocates cash flows into regulatory time buckets, and estimates $\Delta EVE$ under the Basel six-scenario shock set.
*   Report $\Delta EVE$ as a percentage of Tier 1 capital and interpret the risk signal of each scenario.

## 2. User Interface Requirements

### Layout and Navigation Structure

The application will feature a clear and intuitive layout:
*   **Sidebar:** Will host input controls for model parameters, scenario selection, and potentially file upload/download options.
*   **Main Content Area:** Will display the simulation results, including tables, charts, and summary metrics.
*   **Sections:** The main content area will be logically divided into collapsible sections (e.g., "Portfolio Generation", "Cash Flow Analysis", "IRRBB Simulation Results") using Streamlit's `st.expander` to manage content density.

### Input Widgets and Controls

Users will interact with the application through the following widgets, primarily located in the sidebar:
*   **Portfolio Generation Parameters:**
    *   `Number of Instruments`: `st.number_input` (Integer, default 25).
    *   `Tier 1 Capital (TWD)`: `st.number_input` (Float, default 1,000,000,000).
    *   `Portfolio Start Date`: `st.date_input` (Date, default "2023-01-01").
    *   `Portfolio End Date`: `st.date_input` (Date, default "2050-12-31").
*   **Model Parameters:**
    *   `Liquidity Spread (bps)`: `st.number_input` (Integer, default 10).
    *   `Mortgage Prepayment Rate (Annual)`: `st.number_input` (Float, default 0.05).
    *   `NMD Beta`: `st.number_input` (Float, default 0.5).
    *   `NMD Behavioral Maturity (Years)`: `st.number_input` (Float, default 3.0).
    *   `Behavioral Shock Adjustment Factor`: `st.number_input` (Float, default 0.10).
*   **Action Button:**
    *   `Run IRRBB Simulation`: `st.button` to trigger the entire simulation pipeline.

### Visualization Components

The application will present key outputs through the following visual components:
*   **Tables:**
    *   `Generated Synthetic Banking Book Portfolio`: Display of `taiwan_portfolio_df.head()`.
    *   `Baseline Discount Curve`: Display of `baseline_discount_curve_df`.
    *   `First N rows of Cash Flows with Basel Buckets`: Display of `bucketted_cash_flows_df.head(N)`.
    *   `Net Gap Table`: Display of `net_gap_table_df`.
    *   `Delta EVE Report (% of Tier 1 Capital)`: Display of `delta_eve_report_df`.
*   **Charts:**
    *   `Delta EVE by Basel Interest Rate Shock Scenario`: Bar chart generated using `plot_delta_eve_bar_chart` from `delta_eve_report_df`.
*   **Summary Metrics:** Display of `Baseline EVE`, `Total Cash Flows Generated`, `Total Instruments`, and `Scenarios Analyzed`.

### Interactive Elements and Feedback Mechanisms

*   **Loading Indicator:** A `st.spinner` or `st.progress` bar will be displayed while the simulation is running to provide feedback on progress.
*   **Success/Error Messages:** `st.success` or `st.error` messages will indicate the completion status or any issues encountered during processing.
*   **Input Validation:** Implement basic validation (e.g., `start_date` must be before `end_date`, positive numerical inputs).
*   **Download Buttons:** Provide `st.download_button` for `Taiwan_Portfolio.csv`, `gap_table.parquet`, and `irrbb_gap_eve_model.pkl`.

## 3. Additional Requirements

### Annotation and Tooltip Specifications

*   **Input Field Tooltips:** All numerical and date input fields will have tooltips (`help` argument in Streamlit widgets) explaining their purpose and acceptable range/format.
*   **Section Headers and Explanations:** Use `st.header`, `st.subheader`, and `st.markdown` to provide clear titles and explanatory text for each section of the application, including the mathematical foundations.
*   **Chart Labels and Titles:** All charts will have clear titles and axis labels as defined in the `plot_delta_eve_bar_chart` function.
*   **Key Metric Annotations:** Display explanatory text alongside key metrics like Baseline EVE and Delta EVE results to aid interpretation.

### Save the States of the Fields Properly

*   **Session State Management:** The application will extensively use `st.session_state` to store user inputs and computed results (DataFrames, dictionaries of EVEs, etc.) to ensure that:
    *   User inputs are retained across reruns triggered by other widget interactions.
    *   Expensive computations (e.g., cash flow generation, PV calculation, scenario revaluation) are not re-executed unnecessarily when only display properties or minor parameters change.
*   **Caching:** Decorate idempotent and computationally intensive functions (`generate_synthetic_portfolio`, `create_baseline_discount_curve`, `recalculate_cashflows_and_pv_for_scenario`) with `st.cache_data` or `st.cache_resource` as appropriate, ensuring that inputs determining cache keys are stable.
*   **File Persistence:** The application will persist the `Taiwan_Portfolio.csv`, `gap_table.parquet`, and `irrbb_gap_eve_model.pkl` files to disk as part of the simulation run, and provide download options.

## 4. Notebook Content and Code Requirements

This section details the integration of the Jupyter Notebook's Python code into the Streamlit application, outlining the functions, their parameters, and their roles in the interactive flow.

### 4.1. Core Libraries and Global Constants

**Streamlit Context:** These libraries will be imported at the top of the `app.py` script. Global constants will be defined once.
**Relevant Code:**
```python
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import uuid
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
import seaborn as sns
import pickle
import random
import streamlit as st # New import for Streamlit

# Global Constants/Parameters (some can be user inputs via Streamlit widgets)
# Define the valuation date for the entire analysis
valuation_date = datetime.today()

# Define standard Basel buckets for tenors (in months)
standard_tenors_months = [
    1, 3, 6, 12, 24, 36, 60, 120, 180, 240, 360 # Corresponding to 1M, 3M, 6M, 1Y, 2Y, 3Y, 5Y, 10Y, 15Y, 20Y, 30Y
]

# Market rates for baseline discount curve (fixed for this application)
market_rates_data = {
    '1M': 0.02, '3M': 0.022, '6M': 0.025, '1Y': 0.028, '2Y': 0.03, '3Y': 0.032,
    '5Y': 0.035, '7Y': 0.037, '10Y': 0.04, '15Y': 0.042, '20Y': 0.043, '30Y': 0.044
}

# Basel bucket definitions for gap analysis
basel_bucket_definitions_list = [
    (0, 1, 'M'), (1, 3, 'M'), (3, 6, 'M'), (6, 12, 'M'),
    (1, 2, 'Y'), (2, 3, 'Y'), (3, 5, 'Y'), (5, 10, 'Y'), (10, float('inf'), 'Y')
]

# Shock scenarios definitions (fixed for this application)
shock_scenarios = {
    'Parallel Up': {'short': 200, 'long': 200},  # +200 bps across the curve
    'Parallel Down': {'short': -200, 'long': -200},  # -200 bps across the curve
    'Steepener': {'short': -100, 'long': 100},  # Short rates down 100 bps, long rates up 100 bps
    'Flattener': {'short': 100, 'long': -100},  # Short rates up 100 bps, long rates down 100 bps
    'Short-Up': {'short': 200, 'long': 0},  # Short rates up 200 bps, long unchanged
    'Short-Down': {'short': -200, 'long': 0}  # Short rates down 200 bps, long unchanged
}
```

### 4.2. Utility Functions

**Streamlit Context:** These functions will be defined once at the top level of the `app.py` script. `plot_delta_eve_bar_chart` will use `st.pyplot` to display the chart.
**Relevant Code:**
```python
def save_data_to_csv(dataframe, filename):
    dataframe.to_csv(filename, index=False)

def save_data_to_parquet(dataframe, filename):
    dataframe.to_parquet(filename, index=False)

def save_model_artifact(model_object, filename):
    with open(filename, 'wb') as f:
        pickle.dump(model_object, f)

def plot_delta_eve_bar_chart(delta_eve_percentages):
    plt.figure(figsize=(10, 6))
    ax = sns.barplot(
        x='Scenario',
        y='Delta EVE (% Tier 1 Capital)',
        data=delta_eve_percentages,
        palette="viridis"
    )
    plt.title('Delta EVE by Basel Interest Rate Shock Scenario', fontsize=16)
    plt.xlabel('Scenario', fontsize=12)
    plt.ylabel('Delta EVE (% of Tier 1 Capital)', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    st.pyplot(plt) # Use st.pyplot to display in Streamlit
    plt.close() # Close plot to free memory

def convert_tenor_curve_to_date_curve(tenor_curve_df, valuation_date_for_conversion):
    date_curve_data = []
    for index, row in tenor_curve_df.iterrows():
        tenor_months = row['Tenor_Months']
        rate = row['Discount_Rate']
        target_date = valuation_date_for_conversion + relativedelta(months=tenor_months)
        date_curve_data.append({'date': target_date, 'rate': rate})
    return pd.DataFrame(date_curve_data)
```

### 4.3. Data Generation and Initial Setup

**Mathematical Foundation:**
The objective is to assemble a banking-book positions dataset. This dataset will mimic real-world banking book structures, including various instrument types with their respective financial attributes and behavioral characteristics.
**Streamlit Context:** This function will be called when the "Run Simulation" button is pressed. User inputs from `st.number_input` and `st.date_input` will populate its arguments. The resulting `taiwan_portfolio_df` will be stored in `st.session_state` and displayed using `st.dataframe`.
**Relevant Code:**
```python
@st.cache_data # Cache the generated portfolio
def generate_synthetic_portfolio(num_instruments, tier1_capital, start_date, end_date):
    # ... (function implementation as in notebook) ...
    # Exclude internal variables like 'portfolio_as_of_date' from the final df if not needed for output
    # Ensure final_columns list is exactly as specified in the notebook
    # Convert date columns to datetime objects
    # ... (rest of the function implementation) ...
    data = []
    portfolio_as_of_date = datetime.strptime(start_date, "%Y-%m-%d").strftime("%Y-%m-%d") # Use input start_date as portfolio_as_of_date
    
    # ... (rest of the generation logic) ...

    # Ensure consistent column order
    final_columns = [
        'instrument_id', 'category', 'balance', 'rate_type', 'index', 'spread_bps',
        'current_rate', 'payment_freq', 'maturity_date', 'next_repricing_date',
        'currency', 'embedded_option', 'is_core_NMD', 'behavioral_flag'
    ]
    df = pd.DataFrame(data).reindex(columns=final_columns)

    for col in ['maturity_date', 'next_repricing_date']: # 'start_date' column from notebook not in final_columns
        if col in df.columns:
            df[col] = df[col].apply(lambda x: pd.to_datetime(x) if x != 'N/A' else None)
    
    return df
```
**Key Parameters/Outputs:**
*   **Inputs:** `num_instruments`, `tier1_capital` (value, not used in function but passed as context), `start_date`, `end_date`.
*   **Outputs:** `taiwan_portfolio_df` (stored in `st.session_state`).

### 4.4. Baseline Discount Curve Creation

**Mathematical Foundation:**
The Present Value (PV) of a series of cash flows is the sum of the present values of each individual cash flow. For a single cash flow $CF_t$ received at time $t$, discounted at a rate $r_t$:
$$ PV(CF_t) = \frac{CF_t}{(1 + r_t)^{t}} $$
For a series of cash flows $CF_1, CF_2, \ldots, CF_M$ occurring at times $t_1, t_2, \ldots, t_M$:
$$ PV = \sum_{k=1}^{M} \frac{CF_k}{(1 + r_{t_k})^{t_k}} $$
For EVE calculation, the cash flows will be discounted using a risk-free yield curve plus an appropriate liquidity spread; commercial margins are excluded.
**Streamlit Context:** This function will be called during the simulation process. `liquidity_spread_bps` will be an input from `st.number_input`. The `market_rates_data` and `standard_tenors_months` are internal constants. The output `baseline_discount_curve_df` will be stored in `st.session_state` and displayed using `st.dataframe`.
**Relevant Code:**
```python
@st.cache_data # Cache the discount curve
def create_baseline_discount_curve(valuation_date_param, market_rates, tenors_in_months, liquidity_spread_bps):
    # ... (function implementation as in notebook) ...
    # Note: Renamed valuation_date to valuation_date_param to avoid conflict with global variable if cached.
    # The 'valuation_date' used by functions like calculate_cashflows_for_instrument should come from the global/session state.
    # ... (rest of the function implementation) ...
    # Input Validation and Edge Cases (omitted for brevity here but should be in full code)
    liquidity_spread_decimal = liquidity_spread_bps / 10000.0
    
    # Helper function to parse tenor strings
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
```
**Key Parameters/Outputs:**
*   **Inputs:** `liquidity_spread_bps_val`. `market_rates_data`, `standard_tenors_months` are fixed constants. `valuation_date` (passed as `valuation_date_param` for caching).
*   **Outputs:** `baseline_discount_curve_df`, `baseline_date_curve_df` (stored in `st.session_state`).

### 4.5. Pre-processing and Cash Flow Generation

**Mathematical Foundation:**
Cash flows for each instrument are projected based on their `rate_type` (fixed/floating), `payment_freq`, `maturity_date`, and `next_repricing_date`. Behavioral overlays like mortgage prepayment and NMD beta are applied.
The net gap for each time bucket represents the difference between total cash inflows (from assets) and total cash outflows (from liabilities and derivatives) within that bucket:
$$ Net\ Gap_{\text{bucket } k} = \sum_{\text{assets in bucket } k} CF_{\text{in}} - \sum_{\text{liabilities in bucket } k} CF_{\text{out}} $$
**Streamlit Context:** These functions are called in sequence as part of the simulation. Behavioral parameters (`prepayment_rate_annual_val`, `nmd_beta_val`, `nmd_behavioral_maturity_years_val`) will be inputs from `st.number_input`. `bucketted_cash_flows_df` will be stored in `st.session_state` and its head displayed.
**Relevant Code:**
```python
@st.cache_data(show_spinner="Calculating cash flows...")
def generate_all_cash_flows(portfolio_df, baseline_date_curve_df, valuation_date_param,
                            prepayment_rate_annual_val, nmd_beta_val, nmd_behavioral_maturity_years_val):
    all_cash_flows = pd.DataFrame()
    for index, row in portfolio_df.iterrows():
        # calculate_cashflows_for_instrument is a helper, doesn't need @st.cache_data itself
        instrument_cash_flows = calculate_cashflows_for_instrument(row, baseline_date_curve_df, valuation_date_param)
        if not instrument_cash_flows.empty:
            adjusted_cash_flows = apply_behavioral_assumptions(
                instrument_cash_flows,
                row['behavioral_flag'],
                prepayment_rate_annual_val,
                nmd_beta_val,
                nmd_behavioral_maturity_years_val,
                valuation_date_param # Pass valuation_date for NMD behavioral maturity
            )
            all_cash_flows = pd.concat([all_cash_flows, adjusted_cash_flows], ignore_index=True)
    return all_cash_flows

def calculate_cashflows_for_instrument(instrument_data, baseline_curve, valuation_date_param):
    # ... (function implementation from notebook, requires valuation_date as parameter for relative date calcs) ...
    # Ensure all uses of current_date_for_cf_gen, maturity_date_dt, etc. are correct given valuation_date_param
    # The current notebook code has some hardcoded valuation_date.date() references within this function, 
    # they should be replaced with valuation_date_param.date() for consistency and proper behavior.
    
    # Example snippet adaptation:
    # current_date_for_cf_gen = valuation_date_param.date()
    # while current_payment_due_date <= valuation_date_param.date(): # Replaces hardcoded valuation_date
    # ... (rest of the function) ...
    return pd.DataFrame([]) # Placeholder

def apply_behavioral_assumptions(cashflow_df, behavioral_flag, prepayment_rate_annual, nmd_beta, nmd_behavioral_maturity_years, valuation_date_param):
    # ... (function implementation from notebook, requires valuation_date as parameter for NMD) ...
    # Example snippet adaptation for NMDs:
    # behavioral_maturity_date = valuation_date_param + relativedelta(years=int(nmd_behavioral_maturity_years))
    # ... (rest of the function) ...
    return cashflow_df # Placeholder

@st.cache_data(show_spinner="Mapping cash flows to Basel buckets...")
def map_cashflows_to_basel_buckets(cashflow_df, valuation_date_param, basel_bucket_definitions):
    # ... (function implementation from notebook, requires valuation_date as parameter) ...
    return cashflow_df # Placeholder
```
**Key Parameters/Outputs:**
*   **Inputs:** `taiwan_portfolio_df`, `baseline_date_curve_df`, `valuation_date`, `prepayment_rate_annual_val`, `nmd_beta_val`, `nmd_behavioral_maturity_years_val`, `basel_bucket_definitions_list`.
*   **Outputs:** `all_cash_flows`, `bucketted_cash_flows_df` (both stored in `st.session_state`).

### 4.6. Baseline EVE Calculation and Gap Analysis

**Mathematical Foundation:**
EVE is defined as the present value of all banking book assets minus the present value of all banking book liabilities and off-balance sheet items.
$$ EVE_{\text{baseline}} = \sum_{i=1}^{N_A} PV(CF_{A,i}) - \sum_{j=1}^{N_L} PV(CF_{L,j}) $$
$\Delta EVE$ measures the change in a bank's EVE due to an interest rate shock:
$$ \Delta EVE = EVE_{\text{shocked}} - EVE_{\text{baseline}} $$
**Streamlit Context:** These functions will be called after cash flows are generated and bucketed. The `net_gap_table_df` and `baseline_eve` will be stored in `st.session_state` and displayed. `gap_table.parquet` will be saved and available for download.
**Relevant Code:**
```python
@st.cache_data(show_spinner="Calculating Baseline EVE...")
def calculate_present_value_for_cashflows(cashflow_df, discount_curve, valuation_date_param):
    # ... (function implementation from notebook, uses valuation_date_param) ...
    return 0.0, 0.0 # Placeholder

def calculate_eve(pv_assets, pv_liabilities):
    return pv_assets - pv_liabilities

@st.cache_data(show_spinner="Calculating Net Gap...")
def calculate_net_gap(bucketed_cashflow_df):
    # ... (function implementation from notebook) ...
    return pd.DataFrame() # Placeholder
```
**Key Parameters/Outputs:**
*   **Inputs:** `bucketted_cash_flows_df`, `baseline_discount_curve_df`, `valuation_date`.
*   **Outputs:** `pv_assets_baseline`, `pv_liabilities_baseline`, `baseline_eve`, `net_gap_table_df` (all stored in `st.session_state`).

### 4.7. Scenario Shock Application and Revaluation

**Mathematical Foundation:**
The engine will simulate $\Delta EVE$ under the six prescribed Basel interest rate shock scenarios.
**Streamlit Context:** This section will be executed for each scenario defined in `shock_scenarios`. The main orchestration function `recalculate_cashflows_and_pv_for_scenario` should be cached carefully, as it's the most expensive part. `shocked_eves` will be stored in `st.session_state`.
**Relevant Code:**
```python
@st.cache_data # Cache shocked curve generation
def generate_basel_shocked_curve(baseline_curve, scenario_type, shock_magnitude_bps_short, shock_magnitude_bps_long):
    # ... (function implementation from notebook) ...
    return pd.DataFrame() # Placeholder

def reprice_floating_instrument_cashflows_under_shock(instrument_cashflow_df, instrument_data, shocked_date_curve):
    # ... (function implementation from notebook) ...
    return instrument_cashflow_df # Placeholder

def adjust_behavioral_assumptions_for_shock(cashflow_df, scenario_type, baseline_prepayment_rate, shock_adjustment_factor):
    # ... (function implementation from notebook) ...
    return cashflow_df # Placeholder

@st.cache_data(show_spinner="Recalculating cash flows and PV for scenario...")
def recalculate_cashflows_and_pv_for_scenario(portfolio_df, shocked_curve, valuation_date_param, scenario_type,
                                            baseline_date_curve_df, # Pass baseline_date_curve_df for calculate_cashflows_for_instrument
                                            prepayment_rate_annual_for_shock, behavioral_shock_adjustment_factor,
                                            nmd_beta_val, nmd_behavioral_maturity_years_val):
    # ... (function implementation from notebook, ensuring all dependencies are explicit parameters) ...
    # This function orchestrates calls to calculate_cashflows_for_instrument, reprice_floating_instrument_cashflows_under_shock,
    # and adjust_behavioral_assumptions_for_shock, and finally calculate_present_value_for_cashflows.
    # Make sure all required parameters for sub-functions are correctly passed through.
    
    # Define behavioral parameters local to this function or pass them as arguments
    # prepayment_rate_annual_for_shock, behavioral_shock_adjustment_factor, nmd_beta_val, nmd_behavioral_maturity_years_val
    # (These parameters can be pulled from Streamlit inputs)
    
    # ... (rest of the function) ...
    return 0.0 # Placeholder
```
**Key Parameters/Outputs:**
*   **Inputs:** `taiwan_portfolio_df`, `baseline_discount_curve_df`, `valuation_date`, `shock_scenarios` (internal constant), `prepayment_rate_annual_val`, `behavioral_shock_adjustment_factor`, `nmd_beta_val`, `nmd_behavioral_maturity_years_val`.
*   **Outputs:** `shocked_eves` (dictionary, stored in `st.session_state`).

### 4.8. $\Delta EVE$ Reporting and Model Persistence

**Mathematical Foundation:**
$\Delta EVE$ will be reported as a percentage of Tier 1 capital, allowing for a standardized interpretation of the risk signal:
$$ \Delta EVE (\% \text{ Tier 1 Capital}) = \frac{\Delta EVE}{\text{Tier 1 Capital}} \times 100\% $$
**Streamlit Context:** These functions will be called at the end of the simulation pipeline. The `delta_eve_report_df` will be stored in `st.session_state` and displayed as a table and a bar chart using `st.dataframe` and `st.pyplot`. The `irrbb_gap_eve_model.pkl` will be saved and available for download.
**Relevant Code:**
```python
def calculate_delta_eve(baseline_eve, shocked_eve):
    return shocked_eve - baseline_eve

def report_delta_eve_as_percentage_of_tier1(delta_eve_results, tier1_capital):
    # ... (function implementation from notebook) ...
    return pd.DataFrame() # Placeholder
```
**Key Parameters/Outputs:**
*   **Inputs:** `baseline_eve`, `shocked_eves`, `tier1_capital_val`.
*   **Outputs:** `delta_eve_values`, `delta_eve_report_df` (both stored in `st.session_state`).
*   **Persisted Artifacts:** `irrbb_gap_eve_model.pkl` (contains `valuation_date`, `baseline_discount_curve_df`, `tier1_capital_val`, `baseline_eve`, `shocked_eves`, `delta_eve_report_df`).

The Streamlit application will structure these functions and data flows to provide an interactive and informative user experience for IRRBB EVE simulation.
