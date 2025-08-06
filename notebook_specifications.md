
# Technical Specification for Jupyter Notebook: Interest Rate Risk Navigator

This specification outlines the design and functional requirements for a Jupyter Notebook focused on simulating Interest Rate Risk in the Banking Book (IRRBB). The notebook will guide users through the process of constructing an IRRBB position, applying interest rate shocks, and analyzing the impact on Economic Value of Equity (EVE) and Net Interest Income (NII).

## 1. Notebook Overview

This Jupyter Notebook provides an interactive framework for understanding and calculating Interest Rate Risk in the Banking Book (IRRBB), focusing on Economic Value of Equity (EVE) and Net Interest Income (NII) metrics as per Basel and CBUAE standards.

### 1.1 Learning Goals

Upon completion of this notebook, users will be able to:

*   Construct an IRRBB position dataset that accurately captures interest-sensitive assets, liabilities, and optional derivatives (like swaps), including all necessary attributes for comprehensive cash-flow generation.
*   Generate behavioral cash flows and organize them into a gap table, assigning principal and interest streams to standard Basel time-buckets, and computing bucket-level PV01 (Price Value of 01) or modified duration.
*   Implement a robust cash-flow revaluation IRRBB engine capable of re-pricing the portfolio under the six prescribed Basel interest rate shock curves (Parallel Up, Parallel Down, Steepener, Flattener, Short-end Up, Short-end Down).
*   Output key risk metrics, specifically $\Delta\text{EVE}$ (as a percentage of Tier-1 capital) and 1-year $\Delta\text{NII}$.
*   Interpret the practical meaning of the generated risk metrics (e.g., "$$\Delta\text{EVE} = -5\% \text{ means equity value falls by } 5\% \text{ of Tier-1 if rates rise } 200\text{bp}$$") and identify the underlying drivers of the results.

### 1.2 Expected Outcomes

The notebook is expected to produce the following:

*   **Synthetic Data Generation**: Automatic generation and loading of a synthetic `taiwan_bankbook_positions.csv` dataset, representative of a bank's interest-sensitive balance sheet.
*   **Cash Flow Processing**: A processed dataset containing expanded monthly cash flows for each instrument, incorporating behavioral overlays for mortgages and Non-Maturity Deposits (NMDs).
*   **IRRBB Engine Execution**: Successful execution of an `IRRBBEngine` class that calculates baseline Present Values (PVs) and subsequently revalues the portfolio under each of the six Basel shock scenarios.
*   **Risk Metric Calculation**: Computation of $\Delta\text{EVE}$ (as % Tier-1) and 1-year $\Delta\text{NII}$ for all scenarios.
*   **Visualizations**:
    *   A clear bar chart illustrating the net gap (inflows minus outflows) across different time-buckets under the baseline scenario.
    *   A well-formatted table presenting the calculated $\Delta\text{EVE}$ and $\Delta\text{NII}$ for each shock scenario, facilitating easy interpretation.
*   **Saved Artefacts**: Intermediate and final results will be saved to specified file paths for reproducibility and subsequent use in potential future analysis (e.g., a "Part 2" notebook).

## 2. Mathematical and Theoretical Foundations

This section details the core mathematical concepts and theoretical underpinnings of the IRRBB engine.

### 2.1 Interest Rate Risk in the Banking Book (IRRBB)

Interest Rate Risk in the Banking Book (IRRBB) refers to the current or prospective risk to a bank's capital and earnings arising from adverse movements in interest rates that affect the bank's banking book positions. It is a key prudential risk for banks and is governed by regulations such as those from Basel and CBUAE. This notebook focuses on two primary measures of IRRBB: Economic Value of Equity (EVE) and Net Interest Income (NII).

### 2.2 Economic Value of Equity (EVE)

EVE represents the present value of a bank's assets minus the present value of its liabilities. It is a measure of the long-term impact of interest rate changes on a bank's net worth.

#### Definition
The Economic Value of Equity (EVE) is defined as:
$$
\text{EVE} = \sum_{t=1}^{N} \text{PV}(\text{Assets}_t) - \sum_{t=1}^{N} \text{PV}(\text{Liabilities}_t)
$$
Where $\text{PV}(CF_t)$ is the Present Value of cash flow $CF_t$ at time $t$. The Present Value (PV) of a cash flow stream is calculated using appropriate discount rates:
$$
\text{PV} = \sum_{t=1}^{T} \frac{CF_t}{(1 + r_t)^t} = \sum_{t=1}^{T} CF_t \times DF_t
$$
where $CF_t$ is the cash flow at time $t$, $r_t$ is the discount rate for time $t$, and $DF_t$ is the discount factor for time $t$.

#### Change in EVE ($\Delta\text{EVE}$)
The change in EVE ($\Delta\text{EVE}$) due to an interest rate shock is calculated as:
$$
\Delta\text{EVE} = \text{EVE}_{\text{shock}} - \text{EVE}_{\text{baseline}}
$$
$\Delta\text{EVE}$ is typically reported as a percentage of Tier-1 capital to provide context on its materiality:
$$
\Delta\text{EVE} (\% \text{ Tier-1 Capital}) = \frac{\Delta\text{EVE}}{\text{Tier-1 Capital}} \times 100\%
$$

#### Interpretation
A $\Delta\text{EVE}$ value of, for example, $-5\%$ under a Parallel Up $200\text{bp}$ scenario, means that the economic value of equity is projected to fall by $5\%$ of the bank's Tier-1 capital if interest rates instantaneously rise by $200$ basis points.

### 2.3 Net Interest Income (NII)

Net Interest Income (NII) reflects the difference between the interest earned on a bank's assets and the interest paid on its liabilities over a specific period, typically a 1-year horizon. It is a measure of the short-to-medium term impact of interest rate changes on a bank's profitability.

#### Definition
Net Interest Income (NII) is calculated as:
$$
\text{NII} = \text{Interest Income from Assets} - \text{Interest Expense on Liabilities}
$$
This is an accrual-based measure, meaning it does not involve discounting cash flows.

#### Change in NII ($\Delta\text{NII}$)
The change in NII ($\Delta\text{NII}$) due to an interest rate shock is calculated for a specified horizon (e.g., 1 year):
$$
\Delta\text{NII}_{\text{1-year}} = \text{NII}_{\text{shock, 1-year}} - \text{NII}_{\text{baseline, 1-year}}
$$

#### Interpretation
A $\Delta\text{NII}$ value of, for example, $-10 \text{ million TWD}$ under a Short Rate Down scenario, means that the bank's net interest income for the next 12 months is projected to decrease by $10 \text{ million TWD}$ if short-term rates fall. This typically occurs because assets reprice down faster or to a greater extent than liabilities.

### 2.4 Key Concepts and Methodologies

#### 2.4.1 Cash Flow Generation
The foundation of IRRBB calculation is the accurate projection of cash flows for all interest-sensitive instruments. This involves:
*   **Fixed-Rate Instruments**: Cash flows are known and fixed. Only their present value changes with discount rates.
*   **Floating-Rate Instruments**: Interest payments reset periodically based on a benchmark index (e.g., LIBOR, EIBOR) plus a spread. Cash flows beyond the next reset date are re-projected under the new scenario yield curve.
*   **Non-Maturity Deposits (NMDs)**: These deposits have no contractual maturity. Their behavioral maturity and repricing behavior (NMD beta) are critical for cash flow and interest rate sensitivity.

#### 2.4.2 Discounting and Yield Curves
*   **Baseline Yield Curve**: Represents the current market interest rates across different maturities.
*   **Scenario Yield Curves**: Constructed by applying specific shifts (shocks) to the baseline yield curve.
*   **Discount Factors ($DF_t$)**: Derived from the yield curve, used to bring future cash flows to their present value. For EVE, risk-free rates plus a liquidity spread are used, excluding commercial margins to isolate pure interest rate risk.

#### 2.4.3 Basel Six Shock Scenarios
The notebook implements the six standardized interest rate shock scenarios mandated by Basel:
*   **Parallel Up**: The entire yield curve shifts upwards by a fixed amount (e.g., $+200\text{bp}$).
*   **Parallel Down**: The entire yield curve shifts downwards by a fixed amount (e.g., $-200\text{bp}$).
*   **Steepener**: Short-term rates fall, and long-term rates rise, increasing the slope of the yield curve.
*   **Flattener**: Short-term rates rise, and long-term rates fall, decreasing the slope of the yield curve.
*   **Short-end Up**: Only short-term rates (e.g., up to 1 year) increase, with longer maturities less affected.
*   **Short-end Down**: Only short-term rates (e.g., up to 1 year) decrease, with longer maturities less affected.
These shocks are defined in a `scenarios.yaml` file.

#### 2.4.4 Behavioral Overlays
*   **Mortgage Prepayments**: Mortgages may be prepaid earlier than their contractual maturity, especially if interest rates fall, allowing borrowers to refinance at lower rates. A baseline annual prepayment rate (e.g., $5\%$ p.a.) is assumed, which can be adjusted under different shock scenarios.
*   **Non-Maturity Deposit (NMD) Beta**: NMDs do not reprice 1-for-1 with market rates. The NMD beta represents the proportion of a change in market rates that is passed through to the NMD rate. For example, a beta of $0.5$ means that if market rates rise by $100\text{bp}$, the NMD rate will rise by $50\text{bp}$. Behavioral maturities are also assigned to NMDs for bucketing.

#### 2.4.5 Gap Analysis and PV01
*   **Gap Table**: Organizes cash flows into predefined time buckets (e.g., $0-1\text{M}$, $1-3\text{M}$, $3-6\text{M}$, etc.) and shows the net gap (inflows minus outflows) for each bucket.
*   **PV01 (Price Value of 01)**: Represents the change in the present value of an instrument or portfolio for a 1 basis point ($0.0001$) parallel shift in the yield curve. It quantifies the interest rate sensitivity.
$$
\text{PV01} = -\text{Modified Duration} \times \text{PV} \times 0.0001
$$
While a simplified approach can use gap durations, this notebook will implement a full cash-flow revaluation for pedagogical clarity and accuracy.

## 3. Code Requirements

This section details the expected structure of the code within the Jupyter Notebook, including libraries, data handling, and function definitions. No actual Python code will be written here, only specifications.

### 3.1 Expected Libraries

The following Python libraries are expected to be utilized:

*   `pandas`: For data manipulation and analysis, especially with DataFrames.
*   `numpy`: For numerical operations, array manipulation, and mathematical functions.
*   `yaml`: For loading configuration files, specifically the `scenarios.yaml`.
*   `pickle`: For serializing and de-serializing Python objects (e.g., the `IRRBBEngine` class instance).
*   `matplotlib.pyplot`: For creating static, interactive, and animated visualizations.
*   `seaborn`: For enhancing the aesthetics of matplotlib plots and for more advanced statistical visualizations.

### 3.2 Input/Output Expectations

#### 3.2.1 Input Files
*   `data/taiwan_bankbook_positions.csv`: This is the primary dataset containing the synthetic bank book positions. If this file does not exist, a helper function will generate it.
    *   **Mandatory Columns**: `instrument_id`, `side` (Asset/Liability/OBS), `notional`, `rate_type`, `coupon_or_spread`, `index` (if floating), `payment_freq`, `maturity_date`, `next_reprice_date`, `currency` (TWD), `embedded_option_flag`, `core_flag` (for NMDs).
*   `config/scenarios.yaml`: A YAML file defining the parameters for the six Basel interest rate shock scenarios (e.g., shift magnitudes for different tenors).
*   `config/irrbb_assumptions.yaml`: A YAML file documenting key assumptions like discount curve basis, behavioral rates, and balance sheet treatment.

#### 3.2.2 Output Files
The notebook will save the following intermediate and final artefacts:
*   `data/taiwan_bankbook_positions.csv`: The generated synthetic dataset (if not pre-existing).
*   `interim/irrbb_cashflows.parquet`: A parquet file storing the expanded and processed cash flow DataFrame after applying behavioral overlays and bucketing.
*   `models/irrbb_part1_engine.pkl`: A pickled instance of the `IRRBBEngine` class, containing the state of the engine post-baseline and shock calculations.
*   `outputs/basel_scenario_results.parquet`: A parquet file storing the final calculated $\Delta\text{EVE}$ and $\Delta\text{NII}$ results for all scenarios.

### 3.3 Algorithms and Functions to be Implemented

The notebook will define functions and a class to encapsulate the IRRBB engine logic. No direct Python code will be written here.

#### 3.3.1 Data Generation and Pre-processing
*   **`generate_taiwan_portfolio()`**:
    *   **Purpose**: Creates a synthetic `taiwan_bankbook_positions.csv` file if it doesn't exist.
    *   **Logic**: Randomizes balances/rates while preserving realistic spreads for various instrument types (fixed-rate mortgage, floating-rate corporate loan, term deposit, non-maturity savings, plain-vanilla IRS). Includes behavioral tags and Tier-1 capital figure.
*   **`load_and_preprocess_data(file_path, assumptions_path)`**:
    *   **Purpose**: Loads the raw position data and applies initial pre-processing steps.
    *   **Logic**:
        1.  Reads `taiwan_bankbook_positions.csv` into a pandas DataFrame.
        2.  Filters out non-interest-sensitive assets.
        3.  Expands each instrument's data into a granular, monthly cash flow stream.
        4.  Applies behavioral overlays:
            *   Mortgage prepayment (e.g., $5\%$ p.a. baseline).
            *   NMD beta (e.g., $0.5$ NMD beta) and behavioral maturities for NMDs.
        5.  Stores the intermediate cash flow DataFrame.

#### 3.3.2 `IRRBBEngine` Class
This class will encapsulate the core IRRBB calculation logic.

*   **`__init__(self, positions_df, scenarios_config, assumptions_config)`**:
    *   **Purpose**: Initializes the engine with pre-processed positions, scenario definitions, and behavioral assumptions.
    *   **Parameters**:
        *   `positions_df`: Pandas DataFrame of pre-processed cash flows.
        *   `scenarios_config`: Dictionary loaded from `scenarios.yaml`.
        *   `assumptions_config`: Dictionary loaded from `irrbb_assumptions.yaml`.
*   **`generate_yield_curve(self, base_curve, shock_type, shock_magnitude)`**:
    *   **Purpose**: Constructs a scenario yield curve based on the baseline and specified shock.
    *   **Parameters**: `base_curve`, `shock_type` (e.g., 'Parallel Up'), `shock_magnitude`.
    *   **Output**: A new yield curve (e.g., pandas Series or DataFrame).
*   **`calculate_discount_factors(self, yield_curve, cashflow_dates)`**:
    *   **Purpose**: Computes discount factors for given cash flow dates based on the provided yield curve.
    *   **Logic**: Interpolates discount rates from the yield curve for each cash flow date, then calculates $DF_t = \frac{1}{(1+r_t)^t}$.
*   **`reprice_floating_instruments(self, cashflows_df, scenario_yield_curve)`**:
    *   **Purpose**: Adjusts interest cash flows for floating-rate instruments based on the new scenario yield curve.
    *   **Logic**: For each floating instrument, identifies `next_reprice_date` and re-calculates subsequent interest payments using the scenario yield curve.
*   **`adjust_behavioral_cashflows(self, cashflows_df, scenario_yield_curve)`**:
    *   **Purpose**: Modifies behavioral cash flows (e.g., prepayment, NMD withdrawals) in response to interest rate changes.
    *   **Logic**: If rates fall, increase mortgage prepayment; if rates rise, decrease prepayment. Adjust NMD cash flows based on `NMD beta` and new market rates.
*   **`calculate_present_value(self, cashflows_df, discount_factors_series)`**:
    *   **Purpose**: Calculates the present value of all cash flows (assets and liabilities).
    *   **Logic**: Multiplies each cash flow by its corresponding discount factor and sums them up, separating assets and liabilities.
    *   **Output**: Total PV of assets, Total PV of liabilities.
*   **`calculate_nii(self, cashflows_df, horizon_months=12)`**:
    *   **Purpose**: Calculates the projected Net Interest Income for a specified horizon.
    *   **Logic**: Sums interest income from assets and interest expense from liabilities over the horizon, without discounting.
    *   **Output**: Total NII.
*   **`run_baseline_scenario(self)`**:
    *   **Purpose**: Calculates baseline EVE and NII using current market rates.
    *   **Logic**: Calls `calculate_present_value` and `calculate_nii` with the initial cash flows and baseline yield curve.
*   **`run_shock_scenario(self, scenario_name)`**:
    *   **Purpose**: Applies a specific interest rate shock and calculates $\Delta\text{EVE}$ and $\Delta\text{NII}$.
    *   **Logic**:
        1.  Generates the scenario yield curve using `generate_yield_curve`.
        2.  Calculates new discount factors using `calculate_discount_factors`.
        3.  Reprices floating instruments using `reprice_floating_instruments`.
        4.  Adjusts behavioral cash flows using `adjust_behavioral_cashflows`.
        5.  Calculates scenario EVE and NII using the modified cash flows and discount factors.
        6.  Computes $\Delta\text{EVE}$ and $\Delta\text{NII}$ relative to baseline.
    *   **Output**: Dictionary or DataFrame row with $\Delta\text{EVE}$ (% Tier-1) and $\Delta\text{NII}$ (year 1) for the scenario.
*   **`run_all_scenarios(self)`**:
    *   **Purpose**: Orchestrates the execution of all six Basel shock scenarios.
    *   **Logic**: Iterates through scenarios defined in `scenarios.yaml`, calls `run_shock_scenario` for each, and aggregates results.
    *   **Output**: A pandas DataFrame containing results for all scenarios.

#### 3.3.3 Visualization Functions
*   **`plot_gap_profile(cashflows_df)`**:
    *   **Purpose**: Generates a bar chart of the net gap by time-bucket.
    *   **Logic**: Groups the processed cash flows by predefined time buckets (e.g., Basel buckets), calculates the net sum of inflows and outflows for each, and plots.
*   **`display_scenario_results(results_df, tier1_capital)`**:
    *   **Purpose**: Displays the $\Delta\text{EVE}$ and $\Delta\text{NII}$ results in a clear, formatted table.
    *   **Logic**: Takes the aggregated results DataFrame, calculates $\Delta\text{EVE}$ as a percentage of Tier-1 capital, and applies appropriate formatting (e.g., using `pandas.DataFrame.style.format` for percentages, currency).

### 3.4 Logical Flow of the Notebook

The notebook will follow a clear, sequential flow:

1.  **Notebook Setup and Imports**:
    *   Markdown cell: Title, description, learning outcomes.
    *   Code cell: Import necessary libraries (pandas, numpy, yaml, matplotlib, seaborn, pickle).
    *   Code cell: Define file paths for data, config, and output directories. Ensure output directories exist.

2.  **Theoretical Foundations (Markdown Cells)**:
    *   Detailed explanations of IRRBB, EVE, NII, with LaTeX formulas as specified in Section 2.
    *   Explanation of cash flow generation, discounting, yield curves, and Basel shock scenarios.
    *   Discussion of behavioral overlays and gap analysis.

3.  **Data Loading and Pre-processing**:
    *   Markdown cell: Explain data requirements, synthetic data generation, and pre-processing steps.
    *   Code cell:
        *   Call `generate_taiwan_portfolio()` if `taiwan_bankbook_positions.csv` is not present.
        *   Load `taiwan_bankbook_positions.csv`.
        *   Load `scenarios.yaml` and `irrbb_assumptions.yaml`.
        *   Call `load_and_preprocess_data()` to filter, expand, and apply behavioral overlays.
        *   Display head of the processed cash flow DataFrame.
        *   Save processed cash flows to `interim/irrbb_cashflows.parquet`.

4.  **Baseline Gap Profile Analysis**:
    *   Markdown cell: Explain gap analysis and its importance.
    *   Code cell:
        *   Call `plot_gap_profile()` to visualize the baseline net gap.
        *   Optional: Display a table of PV01 by bucket.

5.  **IRRBB Engine Execution**:
    *   Markdown cell: Introduce the `IRRBBEngine` class and explain its purpose (revaluation under shocks).
    *   Code cell:
        *   Instantiate `IRRBBEngine` with loaded data and configurations.
        *   Call `run_baseline_scenario()` to calculate baseline EVE and NII.
        *   Call `run_all_scenarios()` to execute all Basel shocks and collect results.
        *   Display the raw results DataFrame.
        *   Save `IRRBBEngine` instance to `models/irrbb_part1_engine.pkl`.
        *   Save scenario results to `outputs/basel_scenario_results.parquet`.

6.  **Results Visualization and Interpretation**:
    *   Markdown cell: Explain how to interpret $\Delta\text{EVE}$ and $\Delta\text{NII}$ results.
    *   Code cell:
        *   Call `display_scenario_results()` to present the final, formatted table of $\Delta\text{EVE}$ and $\Delta\text{NII}$ for all scenarios.
        *   Add markdown commentary to interpret specific results (e.g., why Parallel Up causes $\Delta\text{EVE}$ to fall if assets have longer duration than liabilities).

7.  **Conclusion and Hand-off**:
    *   Markdown cell: Summarize the notebook's achievements and reiterate learning outcomes.
    *   Markdown cell: Provide clear instructions on where intermediate and final artefacts are saved, specifically noting the `pickle.load()` and `pd.read_parquet()` for "Part 2" hand-off.

### 3.5 Visualizations to be Generated

*   **Gap Profile Bar Chart**:
    *   **Type**: Bar chart.
    *   **X-axis**: Time Buckets (e.g., 0-1M, 1-3M, 3-6M, 6-12M, 1-2Y, 2-3Y, 3-5Y, 5-10Y, >10Y).
    *   **Y-axis**: Net Gap (Inflows - Outflows) in currency units.
    *   **Purpose**: To show the distribution of interest rate sensitivity across different time horizons under the baseline.

*   **Scenario Results Table**:
    *   **Type**: Pandas DataFrame styled as a table.
    *   **Columns**: `Scenario`, `ΔEVE (% Tier-1)`, `ΔNII (Year 1)`.
    *   **Rows**: Each of the six Basel shock scenarios.
    *   **Formatting**:
        *   `ΔEVE (% Tier-1)`: Formatted as a percentage with 1-2 decimal places.
        *   `ΔNII (Year 1)`: Formatted as currency (e.g., TWD) with appropriate delimiters and no decimal places for large figures.
    *   **Purpose**: To provide a clear and concise summary of the impact of each interest rate shock on the bank's economic value and earnings.

## 4. Additional Notes or Instructions

### 4.1 Assumptions

The model implemented in this notebook operates under the following key assumptions:

*   **Static Balance Sheet**: The analysis assumes a static balance sheet, meaning there is no new business growth, and existing instruments run off at their contractual or behavioral maturities without replacement, unless explicitly specified for a particular behavioral overlay.
*   **Single Currency**: For simplicity, all instruments are assumed to be in a single currency (Taiwan Dollar - TWD). Multi-currency aggregation complexities are not covered.
*   **Discount Curve Basis**: For EVE calculations, cash flows are discounted using a risk-free rate (approximated by market yield curves) plus an appropriate liquidity spread. Commercial margins are explicitly excluded to isolate pure interest rate risk.
*   **Behavioral Rates**: Specific behavioral assumptions are hard-coded or configured via `irrbb_assumptions.yaml`:
    *   Mortgage Prepayment: A baseline annual prepayment rate of $5\%$ p.a. is applied. This rate adjusts dynamically based on the direction of interest rate shocks (e.g., higher prepayment if rates fall, lower if rates rise).
    *   NMD Beta: A Non-Maturity Deposit (NMD) beta of $0.5$ is applied, meaning $50\%$ of market rate changes are passed through to NMD rates.
*   **Instantaneous Shocks**: Interest rate shocks for EVE calculations are assumed to be instantaneous and permanent.
*   **NII Horizon**: Net Interest Income calculations are performed over a 1-year horizon.
*   **No Credit Spread Movements**: The model does not account for changes in credit spreads, focusing solely on the impact of risk-free rate movements.
*   **No Volume Shifts**: The analysis focuses on rate effects; volume shifts due to behavioral responses are simplified or ignored to maintain a static balance sheet for the purpose of this exercise.

### 4.2 Constraints

*   **Synthetic Data Only**: The notebook relies solely on a synthetic dataset for demonstration purposes and does not connect to real-world financial systems or customer data.
*   **Fixed Basel Scenarios**: The six Basel interest rate shock scenarios are hard-coded and loaded from `scenarios.yaml`; custom or dynamic scenario generation is not a primary feature.
*   **No User Input UI**: Interaction is via modifying code cells directly; there is no graphical user interface (GUI) for input parameters.

### 4.3 Customization Instructions

Users can modify certain aspects of the model within the notebook's code cells to explore different scenarios or sensitivities:

*   **Behavioral Overlay Parameters**: The baseline mortgage prepayment rate and NMD beta can be adjusted within the `irrbb_assumptions.yaml` file or directly in the code where the `IRRBBEngine` is initialized.
*   **NII Horizon**: The `horizon_months` parameter in the `calculate_nii` function can be changed to analyze NII for different timeframes (e.g., 3 years).
*   **Synthetic Data Generation**: Users can inspect and modify the `generate_taiwan_portfolio()` function to understand how the synthetic data is created and potentially introduce different instrument types or characteristics.

### 4.4 Hand-off to Future Development (Part 2)

This notebook is designed as "Part 1" of a larger project. The following artefacts are explicitly saved for seamless integration into a "Part 2" or subsequent analysis:

*   **IRRBB Engine Object**: The `IRRBBEngine` class instance, containing the calculated baseline and shocked states, is saved as a pickled object: `models/irrbb_part1_engine.pkl`. Future notebooks can load this object using `pickle.load()` to continue analysis without re-running the full engine.
*   **Scenario Results**: The comprehensive DataFrame containing the $\Delta\text{EVE}$ and $\Delta\text{NII}$ results for all Basel scenarios is saved as a parquet file: `outputs/basel_scenario_results.parquet`. This file can be easily loaded using `pd.read_parquet()` for further visualization, reporting, or advanced analysis.
*   **Cash Flow Data**: The expanded and pre-processed cash flows are saved to `interim/irrbb_cashflows.parquet` for granular analysis in subsequent steps.
