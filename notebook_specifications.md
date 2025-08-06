
# Technical Specification: IRRBB Core Engine Simulator (Jupyter Notebook)

## Notebook Title: `IRRBB_Model_Development_Part1.ipynb`

---

## 1. Notebook Overview

This Jupyter Notebook provides a comprehensive simulation framework for understanding Interest Rate Risk in the Banking Book (IRRBB), focusing on the Economic Value of Equity (EVE) metric. It guides users through the process of setting up a banking book, generating cash flows, applying regulatory interest rate shock scenarios, and calculating the resultant change in EVE.

### Learning Goals

Upon completion of this notebook, users will be able to:

*   Assemble a banking-book positions dataset that captures interest-sensitive assets, liabilities, and (optionally) simple hedges.
*   Generate synthetic cash-flow data for those positions, respecting product features and behavioural assumptions.
*   Build a full-revaluation IRRBB engine that computes baseline present values, allocates cash flows into regulatory time buckets, and estimates $\Delta EVE$ under the Basel six-scenario shock set.
*   Report $\Delta EVE$ as a percentage of Tier 1 capital and interpret the risk signal of each scenario.

### Expected Outcomes

*   A synthetically generated banking book portfolio (`Taiwan_Portfolio.csv`) ready for IRRBB analysis.
*   A clear understanding of how interest-sensitive positions are identified and expanded into scheduled cash flows.
*   A `gap_table.parquet` file summarizing net cash flows (inflows minus outflows) across standard Basel time buckets, providing insights into structural interest rate risk.
*   A robust IRRBB engine artifact (`irrbb_gap_eve_model.pkl`) capable of calculating present values under various interest rate scenarios.
*   A comprehensive report on $\Delta EVE$ (change in Economic Value of Equity) for each of the six prescribed Basel interest rate shock scenarios, presented as a percentage of Tier 1 capital, facilitating risk interpretation.

---

## 2. Mathematical and Theoretical Foundations

This section will provide the necessary theoretical background and formulas used in the IRRBB engine, presented using LaTeX.

### 2.1. Interest Rate Risk in the Banking Book (IRRBB)

IRRBB refers to the current or prospective risk to a bank's capital and earnings arising from adverse movements in interest rates that affect the bank’s banking book positions. The primary measures for IRRBB are Economic Value of Equity (EVE) and Net Interest Income (NII). This notebook focuses on EVE.

### 2.2. Economic Value of Equity (EVE)

EVE is defined as the present value of all banking book assets minus the present value of all banking book liabilities and off-balance sheet items. It represents the economic value of a bank, reflecting the present value of its expected future cash flows.

The baseline EVE is calculated as:
$$
EVE_{\text{baseline}} = \sum_{i=1}^{N_A} PV(CF_{A,i}) - \sum_{j=1}^{N_L} PV(CF_{L,j})
$$
where:
*   $N_A$ is the total number of asset positions.
*   $N_L$ is the total number of liability positions.
*   $CF_{A,i}$ represents the cash flows from the $i$-th asset position.
*   $CF_{L,j}$ represents the cash flows from the $j$-th liability position.
*   $PV(\cdot)$ denotes the Present Value calculation.

### 2.3. Present Value (PV) Calculation

The Present Value (PV) of a series of cash flows is the sum of the present values of each individual cash flow. For a single cash flow $CF_t$ received at time $t$, discounted at a rate $r_t$:

$$
PV(CF_t) = \frac{CF_t}{(1 + r_t)^{t}}
$$

For a series of cash flows $CF_1, CF_2, \ldots, CF_M$ occurring at times $t_1, t_2, \ldots, t_M$:
$$
PV = \sum_{k=1}^{M} \frac{CF_k}{(1 + r_{t_k})^{t_k}}
$$
where:
*   $CF_k$ is the cash flow at time $t_k$.
*   $r_{t_k}$ is the appropriate discount rate for time $t_k$.

**Important Note on Discounting:**
For EVE calculation, the cash flows will be discounted using a risk-free yield curve plus an appropriate liquidity spread. Commercial margins and credit spreads will be explicitly excluded from the discount rates to ensure that EVE purely reflects interest rate risk, in line with Basel guidance.

### 2.4. Change in Economic Value of Equity ($\Delta EVE$)

$\Delta EVE$ measures the change in a bank's EVE due to an interest rate shock. It is calculated by re-computing the EVE under a shocked interest rate scenario and subtracting the baseline EVE.

$$
\Delta EVE = EVE_{\text{shocked}} - EVE_{\text{baseline}}
$$

$\Delta EVE$ will be reported as a percentage of Tier 1 capital, allowing for a standardized interpretation of the risk signal:
$$
\Delta EVE (\% \text{ Tier 1 Capital}) = \frac{\Delta EVE}{\text{Tier 1 Capital}} \times 100\%
$$

### 2.5. Cash Flow Generation and Behavioral Assumptions

Cash flows for each instrument are projected based on their `rate_type` (fixed/floating), `payment_freq`, `maturity_date`, and `next_repricing_date`.

*   **Fixed-Rate Instruments:** Cash flows (principal and interest) are static and determined by the initial `current_rate`.
*   **Floating-Rate Instruments:** Interest payments are re-calculated at each `next_repricing_date` based on the prevailing `index` rate plus `spread_bps`. Under shock scenarios, these rates will change.

**Behavioral Overlays:**
*   **Mortgage Prepayment:** A baseline annual prepayment rate (e.g., 5% p.a.) will be applied to mortgage cash flows. This rate may be adjusted under shock scenarios (e.g., higher prepayment in down-rate shocks, lower in up-rate shocks).
*   **Non-Maturity Deposits (NMDs):** NMDs will be assigned a behavioral maturity and repricing beta (e.g., $\beta = 0.5$). This means that for a 1% market rate change, the NMD rate will change by $0.5\% \times 1\% = 0.5\%$. This beta will influence how NMD cash flows reprice under shock scenarios.

### 2.6. Basel Six Interest Rate Shock Scenarios

The engine will simulate $\Delta EVE$ under the following six prescribed Basel interest rate shock scenarios, each generating a new yield curve:

1.  **Parallel Up:** The entire yield curve shifts upwards by a specified basis points (e.g., +200 bp).
2.  **Parallel Down:** The entire yield curve shifts downwards by a specified basis points (e.g., -200 bp).
3.  **Steepener:** Short-term rates fall, and long-term rates rise.
4.  **Flattener:** Short-term rates rise, and long-term rates fall.
5.  **Short-Up:** Short-term rates rise, and long-term rates remain unchanged.
6.  **Short-Down:** Short-term rates fall, and long-term rates remain unchanged.

### 2.7. Net Gap Analysis

The net gap for each time bucket represents the difference between total cash inflows (from assets) and total cash outflows (from liabilities and derivatives) within that bucket. A positive net gap indicates asset sensitivity, while a negative net gap indicates liability sensitivity.

$$
Net\ Gap_{\text{bucket } k} = \sum_{\text{assets in bucket } k} CF_{\text{in}} - \sum_{\text{liabilities in bucket } k} CF_{\text{out}}
$$

### 2.8. PV01 (Optional)

PV01 (Present Value of a One Basis Point) measures the change in present value for a 1 basis point (0.01%) change in interest rates. While the full revaluation approach is primary, for pedagogical purposes, a conceptual understanding or approximation of PV01 for each time bucket might be discussed.

---

## 3. Code Requirements

This section outlines the logical flow, required libraries, input/output, algorithms, and visualization for the Jupyter Notebook.

### 3.1. Expected Libraries

The following Python libraries are expected for data manipulation, numerical operations, and visualization:

*   **`pandas`**: For data structuring (DataFrames), manipulation, and I/O (CSV, Parquet).
*   **`numpy`**: For numerical operations, array manipulation, and mathematical functions.
*   **`matplotlib.pyplot`**: For generating static plots like bar charts.
*   **`seaborn`**: For enhanced data visualizations, building on matplotlib.
*   **`scipy.interpolate`**: Potentially for yield curve interpolation.
*   **`pickle`**: For persisting the model object (`irrbb_gap_eve_model.pkl`).

### 3.2. Input/Output Expectations

*   **Input Data:**
    *   **Synthetic `Taiwan_Portfolio.csv`**: This file will be generated programmatically *within* the notebook based on the specifications. It will not be loaded from an external source but will serve as the initial dataset for the IRRBB engine.
        *   **Size**: Approximately 20-30 rows.
        *   **Core columns**: `instrument_id`, `category` (asset/liability/derivative), `balance`, `rate_type` (fixed/floating), `index` (if floating, e.g., EIBOR), `spread_bps`, `current_rate`, `payment_freq` (e.g., 'Monthly', 'Quarterly', 'Annual'), `maturity_date` (YYYY-MM-DD), `next_repricing_date` (YYYY-MM-DD), `currency`, `embedded_option` (yes/no), `is_core_NMD` (yes/no), `behavioural_flag` (e.g., 'Mortgage_Prepay', 'NMD_Savings').
        *   **Synthetic Generation Rules**: Include at least one fixed-rate mortgage, one floating-rate corporate loan (EIBOR + spread), a term deposit, a non-maturity savings account, and an interest-rate swap. Attributes will follow the core columns.
*   **Output Files:**
    *   **`Taiwan_Portfolio.csv`**: The generated synthetic portfolio, persisted to disk.
    *   **`gap_table.parquet`**: A Parquet file containing the bucketed net gap table, persisted to disk.
    *   **`irrbb_gap_eve_model.pkl`**: A Python pickle file containing the entire IRRBB engine model object, persisted to disk for validation in subsequent parts.

### 3.3. Logical Flow and Algorithms (Without Code)

The notebook will follow a clear, sequential logical flow, with each step explained in a markdown cell followed by a code cell for its implementation.

#### 3.3.1. Section: Data Generation and Initial Setup

*   **Markdown Explanation**: Introduce the need for synthetic data for anonymity and educational purposes. Detail the structure and key attributes of the `Taiwan_Portfolio.csv` to be generated.
*   **Code Section (Conceptual)**:
    *   **Algorithm**: Implement a function or sequence of steps to programmatically generate a synthetic dataset conforming to `datasetDetails`.
        *   Define instrument types (fixed mortgage, floating loan, term deposit, NMD, swap).
        *   Generate realistic values for `instrument_id`, `balance`, `rate_type`, `current_rate`, `maturity_date`, etc., for each instrument type.
        *   Populate `embedded_option`, `is_core_NMD`, `behavioural_flag` as per requirements.
    *   **Output**: A Pandas DataFrame representing `Taiwan_Portfolio.csv`.
    *   **Persistence**: Save this DataFrame to `Taiwan_Portfolio.csv`.

#### 3.3.2. Section: Pre-processing and Cash Flow Generation

*   **Markdown Explanation**: Explain the importance of identifying interest-sensitive positions, expanding them into individual cash flows, applying behavioral assumptions, and mapping these cash flows into regulatory time buckets. Define the Basel time buckets (0-1M, 1-3M, 3-6M, 6-12M, 1-2Y, 2-3Y, 3-5Y, 5-10Y, >10Y).
*   **Code Section (Conceptual)**:
    *   **Algorithm**:
        *   **Identify Interest-Sensitive Positions**: Filter the generated `Taiwan_Portfolio` to retain only instruments sensitive to interest rate changes.
        *   **Cash Flow Expansion**: For each interest-sensitive instrument:
            *   Based on `payment_freq`, `balance`, `current_rate`, `maturity_date`, and `next_repricing_date`, generate a granular schedule of principal and interest cash flows.
            *   For fixed-rate instruments, project all future cash flows.
            *   For floating-rate instruments, project cash flows up to the `next_repricing_date` using the `current_rate`, and beyond that, assume a re-set.
        *   **Apply Behavioral Overlays**:
            *   **Mortgage Prepayment**: Integrate a function to model annual mortgage prepayment (e.g., 5% p.a. baseline), adjusting future principal cash flows accordingly.
            *   **NMD Behavioral Maturity**: Assign NMD cash flows to appropriate time buckets based on an assumed behavioral maturity and beta (e.g., NMD beta = 0.5).
        *   **Map to Basel Buckets**: Allocate each generated cash flow (both principal and interest) into the correct Basel time bucket based on its date.
    *   **Output**: An internal data structure (e.g., a DataFrame) containing detailed cash flows categorized by instrument and time bucket.

#### 3.3.3. Section: Baseline EVE Calculation and Gap Analysis

*   **Markdown Explanation**: Detail the process of calculating baseline present values for all cash flows using the current yield curve. Explain how the net gap is derived from inflows and outflows within each time bucket and its significance.
*   **Code Section (Conceptual)**:
    *   **Algorithm**:
        *   **Baseline Discount Curve**: Define or load a baseline risk-free discount curve (e.g., using observed market rates or a simple synthetic curve). Ensure liquidity spread is added, and commercial margins are excluded.
        *   **Calculate Baseline Present Values**: For every cash flow generated in the previous step, calculate its present value using the baseline discount curve. Aggregate PVs for assets and liabilities separately.
        *   **Baseline EVE**: Compute $EVE_{\text{baseline}}$.
        *   **Gap Analysis**: Sum cash inflows (assets) and cash outflows (liabilities) for each Basel time bucket to compute the net gap for each bucket.
    *   **Output**: Baseline EVE value, and a structured table of net gaps by Basel time bucket.
    *   **Persistence**: Save the net gap table to `gap_table.parquet`.

#### 3.3.4. Section: Scenario Shock Application and Revaluation

*   **Markdown Explanation**: Explain the mechanics of applying the six Basel shock scenarios to the baseline yield curve. Describe how this impacts discount rates and how cash flows for floating-rate instruments and behavioral assumptions are re-projected under these new scenarios.
*   **Code Section (Conceptual)**:
    *   **Algorithm**:
        *   **Generate Shocked Yield Curves**: For each of the six Basel scenarios (Parallel Up/Down, Steepener, Flattener, Short-Up, Short-Down):
            *   Create a new yield curve by applying the specified shock parameters to the baseline curve.
        *   **Re-project Cash Flows Under Shocks**: For each scenario:
            *   **Fixed-Rate Instruments**: Their cash flow amounts remain unchanged, but their present values will change due to the new discount rates.
            *   **Floating-Rate Instruments**: For cash flows beyond the next repricing date, recalculate interest payments based on the new shocked rates from the scenario yield curve.
            *   **Behavioral Adjustments**: If applicable, adjust behavioral assumptions (e.g., prepayment rates) based on the direction and magnitude of the interest rate shock (e.g., lower prepayment in "Parallel Up", higher in "Parallel Down").
        *   **Calculate Shocked Present Values**: Discount all cash flows (re-projected where necessary) using the respective shocked scenario yield curve. Aggregate PVs for assets and liabilities.
        *   **Calculate Shocked EVE**: Compute $EVE_{\text{shocked}}$ for each scenario.

#### 3.3.5. Section: $\Delta EVE$ Reporting and Model Persistence

*   **Markdown Explanation**: Describe how $\Delta EVE$ is calculated for each scenario and presented as a percentage of Tier 1 capital. Explain the interpretation of positive and negative $\Delta EVE$. Conclude by outlining the persistence of the model object for future validation.
*   **Code Section (Conceptual)**:
    *   **Algorithm**:
        *   **Calculate $\Delta EVE$**: For each scenario, subtract the baseline EVE from the shocked EVE ($EVE_{\text{shocked}} - EVE_{\text{baseline}}$).
        *   **Percentage of Tier 1 Capital**: Divide $\Delta EVE$ by a predefined Tier 1 capital value (e.g., a placeholder value can be used if not provided) and express as a percentage.
        *   **Store Metrics**: Store baseline EVE, $\Delta EVE$ per scenario (% Tier 1), and potentially bucket-level PV01 (if implemented).
        *   **Model Persistence**: Serialize the entire IRRBB engine model (or relevant components like parameters, curves, and core functions) into `irrbb_gap_eve_model.pkl` using Python's `pickle` module.
    *   **Output**: A report of $\Delta EVE$ values for all six scenarios, and the `irrbb_gap_eve_model.pkl` file.

### 3.4. Visualization Requirements

The notebook will include code sections to generate the following visualizations:

*   **Net Gap Table**:
    *   **Description**: A tabular summary showing the net gap (cash-in minus cash-out) for each Basel time bucket. This table should be clearly formatted and easy to read.
    *   **Columns**: Basel Time Bucket (e.g., '0-1M', '1-3M', ...), Total Inflows, Total Outflows, Net Gap.
*   **$\Delta EVE$ Bar Chart**:
    *   **Description**: A bar chart displaying the $\Delta EVE$ (as a percentage of Tier 1 capital) for each of the six Basel interest rate shock scenarios.
    *   **Axes**: X-axis showing the six scenario names (e.g., "Parallel Up", "Parallel Down"), Y-axis showing $\Delta EVE$ (%).
    *   **Interpretation**: The chart should visually highlight which scenarios pose the most significant risk (largest negative $\Delta EVE$) or benefit (largest positive $\Delta EVE$).
*   **(Optional Pedagogical Aid) Waterfall Chart for One Scenario**:
    *   **Description**: A waterfall chart illustrating the transition from baseline EVE to shocked EVE for a single, selected scenario (e.g., Parallel Up). This would visually break down the components contributing to the change.

---

## 4. Additional Notes or Instructions

*   **Regulatory Parameters**: When calculating present values, use a **risk-free discount curve** (e.g., derived from government bond yields or swap rates) and add an appropriate liquidity spread. Explicitly exclude commercial margins from these discount rates, focusing purely on interest rate risk.
*   **Behavioral Assumptions**:
    *   Start with a baseline of **5% annual mortgage prepayment**. The model should allow for adjustments to this rate under various shock scenarios.
    *   Use an **NMD beta of 0.5**, meaning Non-Maturity Deposit rates reprice at 50% of the market rate change.
    *   These assumptions should be clearly documented within the notebook's markdown sections, especially in the theoretical foundations or a dedicated assumptions summary.
*   **Performance Goal**: The end-to-end execution time of the notebook should be less than 30 seconds for the specified 20-30 row synthetic dataset. The focus is on clarity and pedagogical value rather than extreme scale.
*   **Model Output Persistence**: Ensure the synthetic dataset (`Taiwan_Portfolio.csv`), the bucketed gap table (`gap_table.parquet`), and the full IRRBB engine model (`irrbb_gap_eve_model.pkl`) are persisted to disk with these exact filenames. These files are critical "validation hooks" for subsequent analytical tasks.
*   **Clarity over Scale**: Prioritize clear, well-commented code and comprehensive markdown explanations over highly optimized or complex implementations, given the educational objective.
*   **No Python Code**: The specification strictly prohibits the inclusion of Python code. All algorithms are described conceptually.

