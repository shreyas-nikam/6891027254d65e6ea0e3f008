
# Streamlit Application Requirements Specification: IRRBB EVE Simulation

## 1. Application Overview

The Streamlit application will serve as an interactive tool for simulating Interest Rate Risk in the Banking Book (IRRBB), with a primary focus on the Economic Value of Equity (EVE). Its core purpose is to enable users to:

*   Generate a synthetic banking book portfolio with interest-sensitive assets, liabilities, and derivatives.
*   Project future cash flows for these positions, incorporating product features and behavioral assumptions (e.g., mortgage prepayments, Non-Maturity Deposit (NMD) behavioral betas).
*   Compute baseline EVE and Net Gap analysis across regulatory time buckets.
*   Estimate the change in EVE ($\Delta EVE$) under the six prescribed Basel interest rate shock scenarios (Parallel Up/Down, Steepener, Flattener, Short-Up/Down).
*   Report $\Delta EVE$ as a percentage of Tier 1 capital, facilitating risk interpretation and regulatory compliance.

The application aims to provide a clear, visual, and interactive demonstration of the IRRBB engine, enhancing understanding of interest rate risk impact on a bank's economic value.

## 2. User Interface Requirements

### Layout and Navigation Structure

The application will feature a clear, intuitive single-page layout.
*   **Sidebar (`st.sidebar`):** Dedicated to user inputs, configuration parameters, and a "Run Simulation" button.
*   **Main Content Area:** Displays the simulation results, including tables, charts, and key metrics, organized into logical sections.

### Input Widgets and Controls

Users will interact with the application through various input widgets:

1.  **Portfolio Generation Parameters:**
    *   **Number of Instruments (`num_instruments`):** `st.sidebar.slider` or `st.sidebar.number_input` (e.g., `range(1, 100)`, default 25).
    *   **Tier 1 Capital (`tier1_capital_val`):** `st.sidebar.number_input` (e.g., default 1,000,000,000 TWD).
    *   **Portfolio Start Date (`start_date_gen`):** `st.sidebar.date_input` (e.g., default "2023-01-01").
    *   **Portfolio End Date (`end_date_gen`):** `st.sidebar.date_input` (e.g., default "2050-12-31").
    *   **Valuation Date (`valuation_date`):** `st.sidebar.date_input` (e.g., default `datetime.today()`).

2.  **Discount Curve Parameters:**
    *   **Liquidity Spread (bps) (`liquidity_spread_bps_val`):** `st.sidebar.slider` or `st.sidebar.number_input` (e.g., `range(0, 100)`, default 10).
    *   (Optional but good to display): Baseline market rates and standard tenors (can be hardcoded initially but displayed for transparency).

3.  **Behavioral Assumption Parameters:**
    *   **Annual Mortgage Prepayment Rate (`prepayment_rate_annual_val`):** `st.sidebar.slider` (e.g., `range(0.0, 0.2, 0.01)`, default 0.05).
    *   **NMD Beta (`nmd_beta_val`):** `st.sidebar.slider` (e.g., `range(0.0, 1.0, 0.05)`, default 0.5).
    *   **NMD Behavioral Maturity (Years) (`nmd_behavioral_maturity_years_val`):** `st.sidebar.slider` (e.g., `range(1.0, 10.0, 0.5)`, default 3.0).
    *   **Behavioral Shock Adjustment Factor (`behavioral_shock_adjustment_factor`):** `st.sidebar.slider` (e.g., `range(0.0, 0.5, 0.01)`, default 0.10).

4.  **Simulation Control:**
    *   **Run Simulation Button:** `st.sidebar.button` to trigger all calculations and display results.

### Visualization Components

The main content area will display key outputs using Streamlit's built-in components:

1.  **Initial Portfolio Overview:**
    *   **Table:** Display the first few rows of the generated `Taiwan_Portfolio.csv` DataFrame. `st.dataframe` or `st.table`.
2.  **Baseline Discount Curve:**
    *   **Table:** Display the `baseline_discount_curve_df`. `st.dataframe`.
3.  **Net Gap Analysis:**
    *   **Table:** Summarizing `Total_Inflows`, `Total_Outflows`, and `Net_Gap` by Basel time bucket (`net_gap_table_df`). `st.table`.
    *   (Optional): Bar chart of `Net_Gap` by bucket.
4.  **Economic Value of Equity (EVE) Results:**
    *   **Key Metrics Display:** `st.metric` or `st.write` to show `Baseline EVE`, `Baseline Present Value of Assets`, and `Baseline Present Value of Liabilities`.
    *   **Table:** Display the `Delta EVE Report (% of Tier 1 Capital)` for all scenarios (`delta_eve_report_df`). `st.table`.
    *   **Bar Chart:** Visualize `Delta EVE by Basel Interest Rate Shock Scenario` (`plot_delta_eve_bar_chart` function output). `st.pyplot`.
    *   (Optional/Future): Waterfall chart illustrating baseline $\rightarrow$ shocked EVE for a selected scenario.

### Interactive Elements and Feedback Mechanisms

*   **Loading Spinner:** `st.spinner("Running simulation...")` to indicate ongoing calculations when the "Run Simulation" button is pressed.
*   **Progress Bar:** `st.progress` to show computation progress during long steps (e.g., cash flow generation).
*   **Info/Success Messages:** `st.info` or `st.success` for successful operations (e.g., "Simulation complete!").
*   **Error Handling:** `st.error` for invalid inputs or calculation issues.
*   **Expanders:** `st.expander` to collapse/expand detailed tables (e.g., raw cash flows) or theoretical explanations.

## 3. Additional Requirements

*   **Real-time Updates and Responsiveness:** The application should be responsive, with calculations completing within the specified performance goal ($< 30$s for a 20-row dataset). Results should update dynamically as parameters are changed and the simulation is re-run.
*   **Annotation and Tooltip Specifications:**
    *   **Mathematical Definitions:** Markdown sections using `st.markdown` and `st.latex` will clearly present the mathematical and theoretical foundations for EVE, PV, $\Delta EVE$, and Net Gap.
        *   Example LaTeX display equations:
            $$ EVE_{\text{baseline}} = \sum_{i=1}^{N_A} PV(CF_{A,i}) - \sum_{j=1}^{N_L} PV(CF_{L,j}) $$
            $$ PV(CF_t) = \frac{CF_t}{(1 + r_t)^{t}} $$
            $$ PV = \sum_{k=1}^{M} \frac{CF_k}{(1 + r_{t_k})^{t_k}} $$
            $$ \Delta EVE = EVE_{\text{shocked}} - EVE_{\text{baseline}} $$
            $$ \Delta EVE (\% \text{ Tier 1 Capital}) = \frac{\Delta EVE}{\text{Tier 1 Capital}} \times 100\% $$
            $$ Net\ Gap_{\text{bucket } k} = \sum_{\text{assets in bucket } k} CF_{\text{in}} - \sum_{\text{liabilities in bucket } k} CF_{\text{out}} $$
        *   Example inline LaTeX: "The discount rate for time $t_k$ is represented by $r_{t_k}$."
    *   **Parameter Explanations:** Short descriptions or `st.help` functions next to input widgets explaining their purpose (e.g., "Liquidity spread (bps): An additional spread applied to the risk-free discount curve.").
    *   **Chart Interpretation:** Concise explanations below charts interpreting the displayed data (e.g., "A negative $\Delta EVE$ indicates a decrease in economic value under the shock scenario.").

## 4. Notebook Content and Code Requirements

This section outlines the essential Python functions and data structures from the Jupyter Notebook that will be integrated into the Streamlit application. The Streamlit app will orchestrate the calls to these functions based on user inputs.

### 4.1. Environment Setup and Libraries

All necessary libraries should be imported at the top of the Streamlit script.

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
```

### 4.2. Mathematical and Theoretical Foundations

These sections will be rendered using `st.markdown` for text and `st.latex` for the mathematical formulas to ensure correct LaTeX formatting.

*   **IRRBB Introduction:** Markdown text explaining IRRBB and its importance.
*   **Economic Value of Equity (EVE):** Markdown text defining EVE, followed by its formula.
    *   `st.latex(r" EVE_{\text{baseline}} = \sum_{i=1}^{N_A} PV(CF_{A,i}) - \sum_{j=1}^{N_L} PV(CF_{L,j}) ")`
*   **Present Value (PV) Calculation:** Markdown text defining PV, followed by its formulas.
    *   `st.latex(r" PV(CF_t) = \frac{CF_t}{(1 + r_t)^{t}} ")`
    *   `st.latex(r" PV = \sum_{k=1}^{M} \frac{CF_k}{(1 + r_{t_k})^{t_k}} ")`
    *   Important Note on Discounting: Text explaining risk-free curve + liquidity spread, excluding commercial margins.
*   **Change in Economic Value of Equity ($\Delta EVE$):** Markdown text defining $\Delta EVE$, followed by its formulas.
    *   `st.latex(r" \Delta EVE = EVE_{\text{shocked}} - EVE_{\text{baseline}} ")`
    *   `st.latex(r" \Delta EVE (\% \text{ Tier 1 Capital}) = \frac{\Delta EVE}{\text{Tier 1 Capital}} \times 100\% ")`
*   **Cash Flow Generation and Behavioral Assumptions:** Markdown text explaining these concepts, including fixed/floating rates, mortgage prepayment, and NMD beta ($\beta$).
*   **Basel Six Interest Rate Shock Scenarios:** List of the six scenarios.
*   **Net Gap Analysis:** Markdown text defining Net Gap, followed by its formula.
    *   `st.latex(r" Net\ Gap_{\text{bucket } k} = \sum_{\text{assets in bucket } k} CF_{\text{in}} - \sum_{\text{liabilities in bucket } k} CF_{\text{out}} ")`

### 4.3. Utility Functions

The following utility functions will be included in the Streamlit script, primarily for plot generation and potentially for caching data. File saving functions (`save_data_to_csv`, `save_data_to_parquet`, `save_model_artifact`) are not directly needed for the interactive UI but can be included for completeness or if artifacts are downloaded.

*   `plot_delta_eve_bar_chart(delta_eve_percentages)`: This function will be called directly, and its `matplotlib.pyplot` figure will be rendered using `st.pyplot()`.

```python
# From Jupyter Notebook: 3.1. Utility Functions
def plot_delta_eve_bar_chart(delta_eve_percentages):
    # ... (function body as in notebook) ...
    # Streamlit will then call st.pyplot(plt.gcf()) after this function completes
```

### 4.4. Core IRRBB Engine Functions

All primary calculation functions from the notebook will be included. They should ideally be wrapped in `st.cache_data` or `st.cache_resource` decorators where appropriate to optimize performance if inputs do not change often.

**4.4.1. Data Generation and Initial Setup**

*   **`generate_synthetic_portfolio(num_instruments, tier1_capital, start_date, end_date)`:**
    *   Purpose: Creates the initial banking book DataFrame (`taiwan_portfolio_df`).
    *   Streamlit Integration: Called once based on user inputs in the sidebar. The generated DataFrame can be displayed using `st.dataframe`.

**4.4.2. Baseline Discount Curve Creation**

*   **`create_baseline_discount_curve(valuation_date, market_rates, tenors_in_months, liquidity_spread_bps)`:**
    *   Purpose: Constructs the `baseline_discount_curve_df`.
    *   Streamlit Integration: Called with user-defined `valuation_date` and `liquidity_spread_bps_val`, using pre-defined `market_rates_data` and `standard_tenors_months`. The resulting `baseline_discount_curve_df` can be displayed.
*   **`convert_tenor_curve_to_date_curve(tenor_curve_df, valuation_date_for_conversion)`:**
    *   Purpose: Helper to convert tenor-based curves to date-based curves needed for cash flow generation.
    *   Streamlit Integration: Called internally by the application logic.

**4.4.3. Pre-processing and Cash Flow Generation**

*   **`calculate_cashflows_for_instrument(instrument_data, baseline_curve)`:**
    *   Purpose: Projects cash flows for a single instrument.
    *   Streamlit Integration: Called iteratively within the main simulation loop for each instrument.
*   **`apply_behavioral_assumptions(cashflow_df, behavioral_flag, prepayment_rate_annual, nmd_beta, nmd_behavioral_maturity_years)`:**
    *   Purpose: Applies behavioral overlays to cash flows.
    *   Streamlit Integration: Called within the main simulation loop with user-defined behavioral parameters (`prepayment_rate_annual_val`, `nmd_beta_val`, `nmd_behavioral_maturity_years_val`).
*   **`map_cashflows_to_basel_buckets(cashflow_df, valuation_date, basel_bucket_definitions)`:**
    *   Purpose: Categorizes cash flows into Basel time buckets.
    *   Streamlit Integration: Called to produce `bucketted_cash_flows_df`.
    *   **Constant:** `basel_bucket_definitions_list` (hardcoded).

**4.4.4. Baseline EVE Calculation and Gap Analysis**

*   **`calculate_present_value_for_cashflows(cashflow_df, discount_curve, valuation_date)`:**
    *   Purpose: Calculates present values.
    *   Streamlit Integration: Used for both baseline and shocked EVE calculations.
*   **`calculate_eve(pv_assets, pv_liabilities)`:**
    *   Purpose: Computes EVE.
    *   Streamlit Integration: Called to get `baseline_eve` and `eve_shocked`.
*   **`calculate_net_gap(bucketed_cashflow_df)`:**
    *   Purpose: Aggregates cash flows into a net gap table (`net_gap_table_df`).
    *   Streamlit Integration: Called to produce the table displayed via `st.table`.

**4.4.5. Scenario Shock Application and Revaluation**

*   **`generate_basel_shocked_curve(baseline_curve, scenario_type, shock_magnitude_bps_short, shock_magnitude_bps_long)`:**
    *   Purpose: Generates shocked yield curves for each Basel scenario.
    *   Streamlit Integration: Called for each selected scenario.
    *   **Constant:** `shock_scenarios` dictionary (hardcoded).
*   **`reprice_floating_instrument_cashflows_under_shock(instrument_cashflow_df, instrument_data, shocked_date_curve)`:**
    *   Purpose: Reprices floating-rate cash flows under a shocked curve.
    *   Streamlit Integration: Called within the `recalculate_cashflows_and_pv_for_scenario` function.
*   **`adjust_behavioral_assumptions_for_shock(cashflow_df, scenario_type, baseline_prepayment_rate, shock_adjustment_factor)`:**
    *   Purpose: Adjusts behavioral assumptions (e.g., prepayment) under shock.
    *   Streamlit Integration: Called within the `recalculate_cashflows_and_pv_for_scenario` function with user-defined `behavioral_shock_adjustment_factor`.
*   **`recalculate_cashflows_and_pv_for_scenario(portfolio_df, shocked_curve, valuation_date, scenario_type)`:**
    *   Purpose: Orchestrates the re-projection and revaluation for an entire scenario.
    *   Streamlit Integration: The central function called for each Basel shock scenario to obtain `eve_shocked`.

**4.4.6. $\Delta EVE$ Reporting**

*   **`calculate_delta_eve(baseline_eve, shocked_eve)`:**
    *   Purpose: Computes absolute $\Delta EVE$.
    *   Streamlit Integration: Called for each scenario's `shocked_eve`.
*   **`report_delta_eve_as_percentage_of_tier1(delta_eve_results, tier1_capital)`:**
    *   Purpose: Converts $\Delta EVE$ to a percentage of Tier 1 capital for reporting.
    *   Streamlit Integration: Called to produce the final `delta_eve_report_df` table and data for the bar chart.

### 4.5. Overall Application Flow (within `st.button` callback)

1.  Retrieve all user inputs from sidebar widgets.
2.  Call `generate_synthetic_portfolio` to create `taiwan_portfolio_df`.
3.  Call `create_baseline_discount_curve` and `convert_tenor_curve_to_date_curve` to get `baseline_discount_curve_df` and `baseline_date_curve_df`.
4.  Iterate `taiwan_portfolio_df` to generate `all_cash_flows` using `calculate_cashflows_for_instrument` and `apply_behavioral_assumptions`.
5.  Call `map_cashflows_to_basel_buckets` to get `bucketted_cash_flows_df`.
6.  Calculate `baseline_eve`, `pv_assets_baseline`, `pv_liabilities_baseline` using `calculate_present_value_for_cashflows` and `calculate_eve`.
7.  Calculate `net_gap_table_df` using `calculate_net_gap`.
8.  Loop through `shock_scenarios`:
    *   Call `generate_basel_shocked_curve` for each `scenario_name`.
    *   Call `recalculate_cashflows_and_pv_for_scenario` to get `eve_shocked` for the current scenario. Store `shocked_eves`.
9.  Call `calculate_delta_eve` for all scenarios to get `delta_eve_values`.
10. Call `report_delta_eve_as_percentage_of_tier1` to get `delta_eve_report_df`.
11. Display all results in the main content area using `st.dataframe`, `st.table`, `st.pyplot`, `st.write`.

The `irrbb_model_artifact` dictionary and the `save_model_artifact` function from the notebook are primarily for persistence outside the Streamlit UI, but could be adapted for a "Download Model" feature if desired.
