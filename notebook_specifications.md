
# IRRBB Sensitivity Analyzer - Jupyter Notebook Specification

## 1. Notebook Overview

**Learning Goals:**

This Jupyter Notebook aims to provide an interactive environment for users to understand and analyze Interest Rate Risk in the Banking Book (IRRBB). Users will learn to:

*   Explain the regulatory objective of the IRRBB framework and the risk types it captures (gap, basis, option risk).
*   Ingest and structure an interest-sensitive banking-book portfolio into a position table.
*   Revalue the portfolio under the six Basel shock scenarios and calculate ΔEVE and ΔNII.
*   Summarize and interpret model outputs to pinpoint the drivers of interest-rate risk.

**Expected Outcomes:**

Upon completing this notebook, users will be able to:

*   Quantify the impact of various interest rate shocks on a bank's Economic Value of Equity (ΔEVE) and Net Interest Income (ΔNII).
*   Identify key vulnerabilities within the banking book related to gap risk, basis risk, and option risk.
*   Interpret sensitivity analyses and understand the term structure of interest rate risk.

## 2. Mathematical and Theoretical Foundations

This section provides the theoretical background for IRRBB analysis, including key formulas and definitions.

**2.1 Economic Value of Equity (ΔEVE)**

The Economic Value of Equity (EVE) represents the difference between the present value of assets and the present value of liabilities. The change in EVE (ΔEVE) due to an interest rate shock is calculated as:

$$
\Delta EVE = EVE_{Scenario} - EVE_{Baseline}
$$

Where:

*   $EVE_{Scenario}$ is the Economic Value of Equity under a specific interest rate scenario.
*   $EVE_{Baseline}$ is the Economic Value of Equity under the baseline interest rate scenario.

ΔEVE is often expressed as a percentage of the bank's equity capital to provide a relative measure of the impact.

**Real-World Application:** Banks use ΔEVE to assess the long-term impact of interest rate changes on their capital adequacy. A significant negative ΔEVE indicates that the bank's economic value is highly sensitive to interest rate increases, potentially leading to regulatory concerns.

**2.2 Net Interest Income (ΔNII)**

Net Interest Income (NII) is the difference between interest income and interest expense. The change in NII (ΔNII) over a specific period (e.g., 1 year or 3 years) due to an interest rate shock is calculated as:

$$
\Delta NII = NII_{Scenario} - NII_{Baseline}
$$

Where:

*   $NII_{Scenario}$ is the Net Interest Income under a specific interest rate scenario.
*   $NII_{Baseline}$ is the Net Interest Income under the baseline interest rate scenario.

**Real-World Application:** Banks use ΔNII to assess the short-term impact of interest rate changes on their profitability. A significant negative ΔNII indicates that the bank's earnings are highly sensitive to interest rate decreases, potentially affecting dividend payouts and shareholder value.

**2.3 Present Value (PV)**

The present value of a future cash flow is its value today, discounted at an appropriate interest rate.  The present value formula is:

$$
PV = \sum_{t=1}^{n} \frac{CF_t}{(1 + r_t)^t}
$$

Where:

*   $CF_t$ is the cash flow in period $t$.
*   $r_t$ is the discount rate for period $t$.
*   $n$ is the number of periods.

**Real-World Application:** Present value calculations are used to determine the fair value of assets and liabilities, considering the time value of money. In IRRBB modeling, present values are re-calculated under various scenarios to assess the impact of interest rate changes.

**2.4 Partial PV01**

Partial PV01 (Price Value of One Basis Point) measures the change in the present value of a portfolio or instrument due to a 1 basis point change in interest rates. It is often calculated for specific time buckets to understand the term structure of interest rate sensitivity.

$$
PV01 = \frac{PV_{-1bp} - PV_{+1bp}}{2}
$$

Where:

*   $PV_{+1bp}$ is the present value after increasing interest rates by 1 basis point.
*   $PV_{-1bp}$ is the present value after decreasing interest rates by 1 basis point.

**Real-World Application:** Partial PV01 helps banks identify the time buckets where they are most exposed to interest rate risk, allowing them to implement hedging strategies to mitigate that risk.

## 3. Code Requirements

**3.1 Libraries:**

The following Python libraries will be used:

*   `pandas`: For data manipulation and analysis, specifically for handling the input portfolio data and storing results.
*   `numpy`: For numerical computations, including cash flow discounting and scenario analysis.
*   `scipy`: For advanced mathematical functions, potentially including curve fitting for yield curve generation.
*   `plotly`: For creating interactive visualizations, including stacked bar charts, diverging bar charts, line charts, and heatmaps.
*   `matplotlib`: As a backup for visualization, and for static plot generation if needed.
*   `pydantic`: For defining data models and validating input data structures (e.g., portfolio positions).

**3.2 Input/Output Expectations:**

*   **Input:**
    *   `Taiwan_IRRBB_Positions.csv`: A CSV file containing the banking book portfolio data.
        *   Mandatory columns: `instrument_id`, `product_type`, `balance` (or `notional`), `current_rate`, `rate_type` (`fixed`/`floating`), `index` (e.g., **TAIBOR**), `spread_bps`, `payment_frequency`, `maturity_date`, `repricing_date`, `currency`, `optionality_flag`, `core_NMD_flag`
        *   Optional behavioural overlays:  `prepayment_rate`, `deposit_beta`, `early_withdrawal_prob`
    *   `taiwan_yield_baseline.csv`: A CSV file containing the baseline yield curve data.
        *   Columns: `tenor`, `shock_name` (containing the baseline yield curve) and scenario curves (parallel ±200 bp, steepener, flattener, short up, short down)
    *   `irrbb_assumptions.yml`: A YAML file defining assumptions related to prepayment rates, deposit betas, discount curve choices, and materiality thresholds.
*   **Output:**
    *   `taiwan_positions_clean.parquet`: A Parquet file containing the cleaned and transformed portfolio data.
    *   `gap_profile.pkl`: A Pickle file containing the gap table and partial PV01 calculations.
    *   `eve_baseline.pkl`: A Pickle file containing the baseline Economic Value of Equity (EVE) calculation.
    *   `irrbb_results.pkl`: A Pickle file containing a dictionary with ΔEVE and ΔNII results for all scenarios.

**3.3 Algorithms and Functions:**

The notebook will implement the following algorithms and functions:

*   **Cash Flow Engine:** A function to generate cash flows for each instrument based on its attributes (e.g., `maturity_date`, `repricing_date`, `payment_frequency`, `current_rate`, `index`, `spread_bps`). This engine should handle both fixed and floating rate instruments.
*   **Gap Analysis:** A function to allocate cash flows to Basel-style time buckets (0-1M, 1-3M, 3-6M, 6-12M, 1-2Y, 2-3Y, 3-5Y, 5-10Y, >10Y) and calculate the net gap (inflows - outflows) for each bucket.
*   **PV01 Calculation:** A function to calculate the partial PV01 for each time bucket.
*   **Scenario Analysis:** A function to apply the six Basel shock scenarios to the yield curve and calculate the resulting ΔEVE and ΔNII. This function should include:
    *   Construction of scenario yield curves based on the baseline yield curve and the specified shock.
    *   Revaluation of assets and liabilities under each scenario.
    *   Calculation of ΔEVE and ΔNII for each scenario.
*   **Data Ingestion:** Function to read data from csv and parse the values, it should be reusable and generic.

**3.4 Visualizations:**

The notebook will generate the following visualizations:

*   **Portfolio Composition:** A stacked bar chart showing the outstanding balance by product type and time bucket.
*   **Gap Profile:** A diverging bar chart showing the net gap (inflows - outflows) across time buckets.
*   **Sensitivity Term Structure:** A line chart showing the partial PV01 per time bucket.
*   **Scenario Impacts:** A summary table with columns for `shock`, `ΔEVE (% of equity)`, `ΔNII (yr 1)`, `ΔNII (yr 3)`, and a conditional-format heatmap highlighting the worst shocks.
*   **Cash-Flow Waterfall:** Waterfall of annual interest income vs expense under baseline vs chosen shock.

## 4. Additional Notes or Instructions

*   **Assumptions:** The notebook will use assumptions defined in the `irrbb_assumptions.yml` file, including prepayment rates, deposit betas, and discount curve choices. These assumptions should be clearly documented and justified.
*   **Constraints:** The notebook should adhere to the Basel time buckets for gap analysis (0-1M, 1-3M, 3-6M, 6-12M, 1-2Y, 2-3Y, 3-5Y, 5-10Y, >10Y).
*   **Customization:** Users should be able to easily modify the input data (e.g., portfolio positions, yield curve data) and assumptions to explore different scenarios and sensitivities.
*   **Modularity:** Follow the modular pipeline as described: `data_ingest.py` →  `cashflow_engine.py` →  `gap_analysis.py` → `eve_model.py` →  `nii_projection.py`.
*   **Naming Convention**: Keep filenames exactly as instructed in the specifications, so that the subsequent parts can load the `.pkl` and other persisted data easily.
