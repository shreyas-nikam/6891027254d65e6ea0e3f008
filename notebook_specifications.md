
# Technical Specification for Jupyter Notebook: IRRBB Gap & PV01 Analyzer

## 1. Notebook Overview

### 1.1 Learning Goals

This Jupyter Notebook aims to provide a comprehensive understanding of Interest Rate Risk in the Banking Book (IRRBB) by guiding users through a practical implementation. Upon completion, users will be able to:

*   **Assemble and Understand Dataset**: Create or load an IRRBB position dataset and identify its cash-flow-relevant attributes for various instruments (loans, deposits, bonds, and optionally interest-rate swaps).
*   **Generate and Allocate Cash Flows**: Simulate contractual and behavioural cash flows for diverse instruments, allocating them into Basel-style repricing buckets.
*   **Build and Interpret Gap Tables**: Construct and analyze a gap table, visualizing net cash inflows versus outflows, and calculating net PV01 (Price Value of 1 Basis Point) or modified duration contributions per bucket.
*   **Calibrate Behavioural Models**: Develop and calibrate two key behavioural sub-models:
    *   A mortgage pre-payment model (e.g., baseline 5% p.a., scenario-sensitive).
    *   A Non-Maturity Deposit (NMD) repricing-beta model (e.g., baseline $\beta = 0.5$).
*   **Implement IRRBB Valuation Engines**: Build full-revaluation IRRBB engines to compute:
    *   Baseline Economic Value of Equity (EVE) and Net Interest Income (NII).
    *   Changes in EVE ($\Delta EVE$) and NII ($\Delta NII$) under the six prescribed Basel shock scenarios (Parallel $\pm$200 bp, Steepener, Flattener, Short Up, Short Down).
*   **Interpret Model Outputs**: Analyze and interpret key risk metrics, such as $\Delta EVE$ as a percentage of Tier 1 capital, and $\Delta NII$ over 1-year and 3-year horizons, and understand their risk-management implications.

### 1.2 Expected Outcomes

The notebook will facilitate the generation of:

*   A synthetic `irrbb_taiwan_positions.csv` dataset, representing a banking book portfolio.
*   A detailed `irrbb_taiwan_cashflows_long.parquet` file containing simulated contractual and behavioural cash flows.
*   An `irrbb_taiwan_gap_table.csv` summarizing bucketed cash inflows, outflows, net gap, and PV01.
*   Calibrated behavioural models (`irrbb_taiwan_mortgage_prepay_model.pkl` and `irrbb_taiwan_nmd_beta_model.pkl`).
*   IRRBB valuation results (`irrbb_taiwan_eve_baseline.pkl`, `irrbb_taiwan_eve_scenarios.pkl`, `irrbb_taiwan_nii_results.pkl`).

In addition to data artifacts, the notebook will display key visualizations:

*   Balance-sheet composition bar chart.
*   Heatmap of the gap table.
*   Term-structure plot of partial PV01.
*   Scenario comparison table for $\Delta EVE$ and $\Delta NII$.
*   (Optional) Waterfall chart illustrating baseline to shocked EVE.

---

## 2. Mathematical and Theoretical Foundations

This section will detail the core mathematical concepts and theoretical underpinnings of IRRBB analysis, with all formulas presented using LaTeX.

### 2.1 Overview of Interest Rate Risk in the Banking Book (IRRBB)

IRRBB refers to the current or prospective risk to a bank’s capital and earnings arising from adverse movements in interest rates that affect the bank’s banking book positions. It primarily arises from:

*   **Gap Risk**: Mismatches in the repricing dates of assets and liabilities.
*   **Basis Risk**: Imperfect correlation in the adjustment of rates for different instruments (e.g., assets repricing on LIBOR vs. liabilities on EIBOR).
*   **Option Risk**: Embedded options in banking book products (e.g., prepayment options on mortgages, early withdrawal options on deposits) that allow customers to alter cash flows based on interest rate movements.

### 2.2 Present Value (PV) and Discounting

The present value of a future cash flow is its value today, discounted at an appropriate interest rate.
The general formula for present value is:
$$ PV = \sum_{t=1}^{N} \frac{CF_t}{(1+r_t)^t} $$
Where:
*   $CF_t$: Cash flow at time $t$.
*   $r_t$: Appropriate discount rate for cash flow at time $t$.
*   $N$: Total number of cash flows.

For IRRBB EVE calculations, the discount rate $r_t$ typically comprises a risk-free rate plus a liquidity spread, excluding any commercial margin, to ensure EVE reflects pure interest rate risk.

### 2.3 Economic Value of Equity (EVE)

EVE measures the change in the economic value of a bank's capital, reflecting the present value of all future cash flows from banking book assets and liabilities.

The baseline EVE is calculated as:
$$ EVE_{baseline} = \sum_{t=1}^{N} \frac{CF_{asset,t}}{(1+r_{baseline,t})^t} - \sum_{t=1}^{M} \frac{CF_{liability,t}}{(1+r_{baseline,t})^t} $$
Where:
*   $CF_{asset,t}$: Cash flow from assets at time $t$.
*   $CF_{liability,t}$: Cash flow from liabilities at time $t$.
*   $r_{baseline,t}$: Baseline discount rate at time $t$.

The change in EVE ($\Delta EVE$) under a shock scenario is calculated as:
$$ \Delta EVE = EVE_{scenario} - EVE_{baseline} $$
Where $EVE_{scenario}$ is calculated using the scenario-specific yield curve.

### 2.4 Net Interest Income (NII)

NII represents the difference between a bank's interest income from assets and its interest expense on liabilities over a specific period (e.g., 1-year or 3-year horizon). It is an accrual-based measure, typically not discounted.

$$ NII = \sum \text{Interest Income (from assets)} - \sum \text{Interest Expense (on liabilities)} $$
The change in NII ($\Delta NII$) under a shock scenario is:
$$ \Delta NII = NII_{scenario} - NII_{baseline} $$

### 2.5 PV01 and Modified Duration

**PV01** (Price Value of 01 Basis Point) is the change in the present value of an instrument or portfolio for a 1 basis point (0.01%) change in interest rates. It is an indicator of interest rate sensitivity.

**Modified Duration ($MD$)** is a measure of the sensitivity of a bond's price to a change in interest rates. It approximates the percentage change in price for a 1% change in yield.
$$ MD = -\frac{1}{PV} \frac{dPV}{dr} $$
The approximate change in Present Value ($\Delta PV$) due to a change in interest rate ($\Delta r$) is given by:
$$ \Delta PV \approx -MD \times PV \times \Delta r $$
Thus, PV01 can be approximated as:
$$ PV01 \approx -MD \times PV \times 0.0001 $$

For gap analysis, the partial PV01 for each bucket indicates which time bands contribute most to EVE sensitivity.

### 2.6 Gap Analysis and Basel Repricing Buckets

Gap analysis categorizes interest-sensitive assets and liabilities into predefined time buckets based on their repricing or maturity dates. The "Net Gap" for each bucket is the difference between cash inflows and outflows.

The Basel-style repricing buckets are typically:
*   0-1 Month (0-1M)
*   1-3 Months (1-3M)
*   3-6 Months (3-6M)
*   6-12 Months (6-12M)
*   1-2 Years (1-2Y)
*   2-3 Years (2-3Y)
*   3-5 Years (3-5Y)
*   5-10 Years (5-10Y)
*   Over 10 Years (>10Y)

$$ Net \, Gap_i = \sum CF_{inflow,i} - \sum CF_{outflow,i} \quad \text{for bucket } i $$

### 2.7 Behavioural Models

To accurately model IRRBB, especially for instruments with embedded options or indeterminate maturities, behavioural models are essential.

#### 2.7.1 Mortgage Prepayment Model

Fixed-rate mortgages often include prepayment options. The model quantifies the likelihood of borrowers prepaying their loans, especially when market interest rates fall below their fixed rate. This can be modeled using a logistic regression or survival model, taking into account factors like the borrower's current rate vs. market rates, loan age, etc.

*   **Baseline Prepayment Rate**: A default annual rate (e.g., 5% p.a.).
*   **Scenario Sensitivity**: Prepayment rates are adjusted under different interest rate scenarios (e.g., higher prepayment in falling rate environments).

#### 2.7.2 Non-Maturity Deposit (NMD) Repricing Beta Model

NMDs (e.g., savings accounts) do not have a contractual maturity. Their effective repricing is behavioral. The beta model describes how the bank's offered rate on NMDs adjusts relative to changes in a benchmark policy rate.

*   **Repricing Beta ($\beta$)**:
    $$ \beta = \frac{\Delta \text{Deposit Rate}}{\Delta \text{Policy Rate}} $$
    A beta of 0.5 means that for every 100 bp change in the policy rate, the deposit rate changes by 50 bp.
*   **Behavioral Maturity**: NMD balances are often assumed to have a "core" portion with a very long or indefinite behavioural maturity and a "non-core" portion that is more sensitive to rate changes or withdrawals.

### 2.8 Interest Rate Shock Scenarios (Basel Prescribed)

The Basel framework mandates specific interest rate shock scenarios to assess IRRBB. These include:

1.  **Parallel Up (+200 bp)**: All points on the yield curve shift up by 200 basis points.
2.  **Parallel Down (-200 bp)**: All points on the yield curve shift down by 200 basis points.
3.  **Steepener**: Short rates fall (e.g., -100 bp), and long rates rise (e.g., +100 bp), steepening the yield curve.
4.  **Flattener**: Short rates rise (e.g., +100 bp), and long rates fall (e.g., -100 bp), flattening the yield curve.
5.  **Short Rate Up**: Only short-term rates increase (e.g., 1-month to 1-year rates).
6.  **Short Rate Down**: Only short-term rates decrease (e.g., 1-month to 1-year rates).

For each scenario, a new yield curve is constructed to derive new discount factors and determine repricing rates for floating-rate instruments.

---

## 3. Code Requirements

This section outlines the logical flow of the notebook and the functionalities required for each part, without providing actual code.

### 3.1 Notebook Logical Flow

The notebook will follow the prescribed outline:

#### **Section 1: Introduction**
*   **Markdown Explanation**: Introduce the notebook's purpose, objectives, and learning goals. Explain the importance of IRRBB management for financial institutions.

#### **Section 2: Data Loading / Synthetic Data Generator**
*   **Markdown Explanation**: Explain the necessity of a robust position dataset. Describe the synthetic data generation process and the structure of `taiwan_irrbb_positions.csv`.
*   **Code Section**:
    *   **User Input**: Prompt user to choose between generating synthetic data or loading an existing `taiwan_irrbb_positions.csv`.
    *   **Synthetic Data Generation Logic**: If chosen, implement a function that generates a pandas DataFrame representing diverse banking book instruments (fixed-rate mortgages, floating-rate corporate loans, term deposits, NMDs, and optionally interest-rate swaps).
        *   Populate `instrument_id`, `instrument_type`, `side`, `notional_amt`, `currency`, `rate_type`, `fixed_rate`, `float_index`, `spread_bps`, `payment_freq`, `maturity_date`, `next_reprice_date`, `optionality_flag`, `core_fraction`, `prepay_rate`.
        *   Ensure a minimum of 1,000 rows.
        *   Randomize balances, coupon/spreads, and payment schedules.
        *   Use ISO 8601 format for all dates.
        *   Save the generated data to `irrbb_taiwan_positions.csv`.
    *   **Data Loading**: Load `irrbb_taiwan_positions.csv` into a pandas DataFrame.

#### **Section 3: Exploratory Data Review**
*   **Markdown Explanation**: Discuss the importance of sanity-checking the loaded data. Explain how to visualize the balance sheet composition.
*   **Code Section**:
    *   Display the head of the loaded DataFrame.
    *   Summarize key statistics (e.g., `df.info()`, `df.describe()`).
    *   **Visualization**: Generate a bar chart showing the balance-sheet composition (notionals by product type and side - asset/liability).

#### **Section 4: Pre-processing & Behavioural Model Calibration**
*   **Markdown Explanation**: Detail the data cleaning steps and the purpose of behavioural models. Explain the conceptual approach for calibrating mortgage prepayment and NMD beta models.
*   **Code Section**:
    *   **Pre-processing Pipeline (`01_data_preparation.py` logic)**:
        *   Clean the loaded DataFrame:
            *   Convert date columns to datetime objects.
            *   Handle missing float spreads (e.g., fill with 0 or a reasonable default based on `rate_type`).
            *   Tag NMDs as 'core' vs. 'non-core' based on specified rules or a `core_fraction` column.
        *   Save the cleaned data to `irrbb_taiwan_clean_positions.pkl`.
    *   **Behavioural Model Calibration**:
        *   **Mortgage Prepayment Model**:
            *   Implement logic to simulate or use synthetic historical prepayment data.
            *   Train a logistic regression or survival model to predict prepayment probabilities.
            *   Save the trained model to `irrbb_taiwan_mortgage_prepay_model.pkl`.
        *   **NMD Beta Model**:
            *   Implement logic to simulate or use synthetic historical policy rate and deposit rate data.
            *   Train a simple Ordinary Least Squares (OLS) model to derive the NMD beta.
            *   Save the trained model to `irrbb_taiwan_nmd_beta_model.pkl`.

#### **Section 5: Cash-flow & Gap Analysis**
*   **Markdown Explanation**: Describe the process of generating cash flows, applying behavioural assumptions, and aggregating them into Basel repricing buckets. Explain how the gap table and partial PV01 are derived and interpreted.
*   **Code Section**:
    *   **Cash Flow Engine (`02_cashflow_engine.py` logic)**:
        *   For each instrument in `irrbb_taiwan_clean_positions.pkl`:
            *   Generate monthly cash flow schedules (principal and interest) based on `notional_amt`, `payment_freq`, `fixed_rate` or `float_index` + `spread_bps`, and `maturity_date`/`next_reprice_date`.
            *   Apply the calibrated mortgage prepayment model to adjust cash flows for fixed-rate mortgages.
            *   Apply early withdrawal assumptions for term deposits.
            *   Apply the calibrated NMD beta model and behavioral maturity assumptions for NMDs.
        *   Store the exploded cash flow schedule in `irrbb_taiwan_cashflows_long.parquet`.
    *   **Gap Table Generation**:
        *   Define standard Basel repricing buckets.
        *   Aggregate cash inflows and outflows from `irrbb_taiwan_cashflows_long.parquet` into these buckets.
        *   Calculate Net Gap (Inflows - Outflows) for each bucket.
        *   Calculate partial PV01 for each bucket (e.g., using bucket mid-points and PVs).
        *   Save the gap table to `irrbb_taiwan_gap_table.csv`.
    *   **Visualizations**:
        *   Generate a heatmap of the `irrbb_taiwan_gap_table.csv`, highlighting repricing mismatches.
        *   Generate a term-structure plot of partial PV01, showing which time bands drive EVE sensitivity.

#### **Section 6: EVE & NII Valuation Engine**
*   **Markdown Explanation**: Detail the methodology for calculating baseline EVE and NII, and how these metrics are re-calculated under various interest rate shock scenarios. Emphasize the full revaluation approach.
*   **Code Section**:
    *   **IRRBB Core Model (`03_irrbb_valuation.py` logic)**:
        *   **Yield Curve Generation**:
            *   Define a baseline yield curve (e.g., TWD risk-free curve).
            *   Construct six scenario yield curves based on Basel shocks (Parallel ±200bp, Steepener, Flattener, Short Up, Short Down).
        *   **Valuation Calculation**:
            *   For each instrument and for the baseline and each shock scenario:
                *   Re-project cash flows considering scenario-specific floating rates and behavioural option exercises (prepayments, withdrawals).
                *   Calculate the present value of all cash flows using the corresponding scenario yield curve (excluding commercial margins).
            *   Compute baseline EVE (PV of assets - PV of liabilities).
            *   Compute EVE for each shock scenario.
            *   Calculate $\Delta EVE$ for each scenario.
            *   Project baseline NII for 1-year and 3-year horizons.
            *   Project NII for each shock scenario for 1-year and 3-year horizons.
            *   Calculate $\Delta NII$ for each scenario and horizon.
        *   Save results: `irrbb_taiwan_eve_baseline.pkl`, `irrbb_taiwan_eve_scenarios.pkl`, `irrbb_taiwan_nii_results.pkl`.

#### **Section 7: Scenario Results & Interpretation**
*   **Markdown Explanation**: Provide guidance on how to interpret the calculated $\Delta EVE$ and $\Delta NII$ results, especially in the context of Basel requirements and Tier 1 capital.
*   **Code Section**:
    *   **Display Results**:
        *   Present a structured table comparing $\Delta EVE$ (as % of Tier 1 capital, requiring a user input for Tier 1 capital) and $\Delta NII$ (1-year and 3-year in TWD) across all scenarios.
        *   (Optional) Generate a waterfall chart illustrating the transition from baseline EVE to shocked EVE for a selected scenario.

#### **Section 8: Save Models and Artifacts**
*   **Markdown Explanation**: Emphasize the importance of persisting all generated models and data artifacts for continuity and potential future use (e.g., Part 2 of an exercise).
*   **Code Section**:
    *   Verify that all required files (`.pkl` model files, `.csv`, `.parquet` outputs) have been saved under a designated `/models/part1/` directory.
    *   Display a checklist of saved artifacts for user confirmation.

### 3.2 Expected Libraries

The notebook will utilize the following Python libraries:

*   `pandas` for data manipulation and analysis.
*   `numpy` for numerical operations.
*   `scipy` for scientific computing, potentially for yield curve interpolation or optimization.
*   `statsmodels` or `scikit-learn` for statistical modeling and behavioural model calibration.
*   `matplotlib.pyplot` and `seaborn` for data visualization.

### 3.3 Input/Output Expectations

*   **Inputs**:
    *   User-defined parameters for synthetic data generation (e.g., number of fixed-rate loans, floating-rate loans, term deposits, NMDs, bonds).
    *   An initial TWD yield curve as the risk-free base.
    *   Tier 1 Capital value for $\Delta EVE$ percentage calculation.
*   **Outputs (Files)**: All output files will use the `irrbb_taiwan_` prefix and be saved under `/models/part1/`.
    *   `irrbb_taiwan_positions.csv`: Initial position dataset.
    *   `irrbb_taiwan_clean_positions.pkl`: Cleaned position dataset.
    *   `irrbb_taiwan_mortgage_prepay_model.pkl`: Calibrated mortgage prepayment model.
    *   `irrbb_taiwan_nmd_beta_model.pkl`: Calibrated NMD beta model.
    *   `irrbb_taiwan_cashflows_long.parquet`: Detailed cash flow schedules.
    *   `irrbb_taiwan_gap_table.csv`: Aggregated gap analysis results.
    *   `irrbb_taiwan_eve_baseline.pkl`: Baseline EVE calculation result.
    *   `irrbb_taiwan_eve_scenarios.pkl`: EVE results for all shock scenarios.
    *   `irrbb_taiwan_nii_results.pkl`: NII results for baseline and all shock scenarios.

### 3.4 Visualizations

The following visualizations will be generated:

*   **Balance-sheet composition bar chart**: Displays notional amounts by instrument type and asset/liability side.
*   **Gap table heat-map**: Visualizes net cash flows across specified time buckets, highlighting repricing mismatches.
*   **Term-structure plot of partial PV01**: Illustrates the contribution of each time bucket to the overall EVE sensitivity.
*   **Scenario comparison table**: A tabular display showing $\Delta EVE$ (as % of Tier 1 capital) and $\Delta NII$ (1-year and 3-year horizons) for all six Basel shock scenarios.
*   **(Optional) Waterfall chart**: A visual breakdown of EVE change from baseline to a selected shock scenario.

---

## 4. Additional Notes or Instructions

### 4.1 Assumptions

*   All dates in generated and processed data will conform to ISO 8601 format.
*   For simplicity, assume a single currency (Taiwanese Dollar, TWD) for most instruments unless explicitly stated otherwise or required for a multi-currency exercise. The TWD yield curve will serve as the risk-free base.
*   A baseline annual prepayment rate for mortgages of 5% p.a. is assumed, adjustable based on interest rate scenarios.
*   A baseline NMD repricing beta ($\beta$) of 0.5 is assumed.
*   For NII projection, a static balance sheet is assumed (no new growth, run-off not replaced).
*   Discount curves used for EVE calculations will exclude commercial margins and incorporate a liquidity spread, aligning with regulatory guidance to isolate pure interest rate risk.
*   All significant assumptions, including those regarding behavioural models and market data, will be explicitly documented inline within the notebook.

### 4.2 Constraints

*   The synthetic data generator must produce a minimum of 1,000 rows, covering specified instrument types and mandatory columns.
*   All output files and saved models must adhere to the `irrbb_taiwan_*` naming convention and be stored persistently under the `/models/part1/` directory.
*   The project will strictly avoid deployment-specific steps or references to external platforms like Streamlit.
*   The specification explicitly prohibits the inclusion of actual Python code.

### 4.3 Customization Instructions

*   Users will be able to specify the number of instruments of each type (e.g., number of fixed-rate mortgages, floating-rate loans) during synthetic data generation.
*   The baseline parameters for behavioural models (e.g., initial mortgage prepayment rate, NMD beta) can be adjusted by the user.
*   The notebook can be extended to include multi-currency analysis by introducing USD or other currency interest rate swaps, if desired, by modifying the synthetic data generation and yield curve management sections.
*   Users can customize visualization parameters (e.g., chart titles, colors) using standard Matplotlib/Seaborn functions.
```
