id: 6891027254d65e6ea0e3f008_documentation
summary: Lab 5.1 IRRBB Models - Development Documentation
feedback link: https://docs.google.com/forms/d/e/1FAIpQLSfWkOK-in_bMMoHSZfcIvAeO58PAH9wrDqcxnJABHaxiDqhSA/viewform?usp=sf_link
environments: Web
status: Published
# QuLab: Interest Rate Risk in the Banking Book (IRRBB) Simulation

## Introduction to IRRBB and QuLab
Duration: 00:07:00

<aside class="positive">
Welcome to QuLab! This codelab will guide you through understanding and interacting with a Streamlit application designed to simulate Interest Rate Risk in the Banking Book (IRRBB), focusing on the Economic Value of Equity (EVE). Understanding IRRBB is crucial for financial institutions to manage their exposure to interest rate fluctuations.
</aside>

### What is IRRBB?
**Interest Rate Risk in the Banking Book (IRRBB)** refers to the current or prospective risk to a bank's capital and earnings arising from adverse movements in interest rates that affect the bank's banking book positions. Unlike trading book risks, which are marked-to-market daily, banking book items are typically held to maturity. This application helps assess how changes in interest rates impact the bank's long-term economic value.

### Key Concepts Explained in QuLab:

*   **Economic Value of Equity (EVE):** The difference between the present value of a bank's interest-rate sensitive assets and the present value of its interest-rate sensitive liabilities. It represents the bank's net worth from an economic perspective, reflecting the long-term impact of interest rate changes on its cash flows.
    $$ EVE_{\text{baseline}} = \sum_{i=1}^{N_A} PV(CF_{A,i}) - \sum_{j=1}^{N_L} PV(CF_{L,j}) $$
    Where:
    *   $N_A$ is the number of assets.
    *   $N_L$ is the number of liabilities.
    *   $PV(CF_{A,i})$ is the present value of the cash flows of asset $i$.
    *   $PV(CF_{L,j})$ is the present value of the cash flows of liability $j$.

*   **Change in Economic Value of Equity ($\Delta EVE$):** This is the primary metric used to quantify IRRBB under different interest rate shock scenarios. It is calculated as the difference between the EVE under a shocked interest rate curve and the baseline EVE.
    $$ \Delta EVE = EVE_{\text{shocked}} - EVE_{\text{baseline}} $$
    Regulators often look at $\Delta EVE$ as a percentage of Tier 1 Capital:
    $$ \Delta EVE (\% \text{ Tier 1 Capital}) = \frac{\Delta EVE}{\text{Tier 1 Capital}} \times 100\% $$

*   **Net Gap Analysis:** A simplified view of interest rate risk, showing the difference between rate-sensitive assets and liabilities within specific time buckets. While less comprehensive than EVE, it provides insights into short-term mismatches.
    $$ Net\ Gap_{\text{bucket } k} = \sum_{\text{assets in bucket } k} CF_{\text{in}} - \sum_{\text{liabilities in bucket } k} CF_{\text{out}} $$

*   **Present Value (PV) Calculation:** The core of EVE calculation involves discounting future cash flows back to the present using an appropriate discount rate.
    $$ PV(CF_t) = \frac{CF_t}{(1 + r_t)^{t}} $$
    or for multiple cash flows:
    $$ PV = \sum_{k=1}^{M} \frac{CF_k}{(1 + r_{t_k})^{t_k}} $$
    Where:
    *   $CF_t$ is the cash flow at time t.
    *   $r_t$ is the discount rate for time t.
    *   $r_{t_k}$ is the discount rate for time $t_k$.

### Application Architecture
The QuLab application is built using Streamlit, a Python framework for creating interactive web applications. It follows a modular design:

*   **`app.py`**: The main entry point for the Streamlit application. It sets up the page configuration, displays the main title, and manages the navigation between different functional pages using a sidebar selectbox. It imports and runs functions from sub-modules for each page.
*   **`application_pages/` directory**: Contains separate Python files for each distinct functional area of the application (e.g., `portfolio_generation.py`, `discount_curve.py`, `irrbb_simulation.py`). This promotes modularity and organization.
*   **`application_pages/utils.py`**: This is the heart of the application's business logic. It contains a collection of helper functions for generating synthetic data, managing interest rate curves, calculating cash flows, applying behavioral assumptions, performing valuations, and simulating interest rate shocks.

```
+--+
|             Streamlit UI          |
|  (User Interaction & Visualization) |
+--+
        |
        V
+--+
|             app.py                |
|  (Main Application, Navigation)   |
+--+
        |  Calls Functions from
        V
+-+
|              application_pages/                             |
|  ++-++ |
|  | portfolio_generation.py | discount_curve.py | irrbb_simulation.py | |
|  | (Generate Portfolio)  | (Manage Curves)   | (Run Simulations) | |
|  ++-++ |
|        |                  |                   |                 |
|        ++-+--+
|                                 Calls Functions from
|                                        V
+-+
|              application_pages/utils.py                     |
|  (Core Logic: Data Gen, Cashflows, PV, Behavioral Models,   |
|   Shock Scenarios, EVE, Net Gap, Reporting)                 |
+-+
```

### Setup and Running the Application

To run this application, you'll need Python installed, preferably in a virtual environment.

1.  **Save the files:** Create the following file structure and save the provided code snippets into their respective files:
    ```
    .
    ├── app.py
    └── application_pages/
        ├── __init__.py  (empty file)
        ├── portfolio_generation.py
        └── utils.py
        ├── discount_curve.py (Placeholder - will need to be created if not provided)
        └── irrbb_simulation.py (Placeholder - will need to be created if not provided)
    ```
    <aside class="negative">
    The code for `application_pages/discount_curve.py` and `application_pages/irrbb_simulation.py` was not provided in the prompt. For this codelab, we will describe their expected functionality based on how `app.py` references them and the functions available in `utils.py`. You may need to create these files with basic Streamlit UI to run the full application.
    </aside>

2.  **Install dependencies:**
    Open your terminal or command prompt and navigate to the root directory of your project (where `app.py` is located). Then run:
    ```console
    pip install streamlit pandas numpy scipy python-dateutil plotly
    ```

3.  **Run the Streamlit application:**
    In the same directory, execute:
    ```console
    streamlit run app.py
    ```
    This command will open the application in your default web browser.

## Exploring the Core Utilities (`utils.py`)
Duration: 00:10:00

The `utils.py` file is where the heavy lifting of the QuLab application happens. It encapsulates all the mathematical models, data generation, and calculation logic. As a developer, understanding this module is key to customizing or extending the application.

Let's break down its key functionalities:

### 1. Data Generation

*   **`generate_synthetic_portfolio(num_instruments, tier1_capital, start_date, end_date)`**:
    This function creates a DataFrame of synthetic financial instruments (Loans, Deposits, Bonds, Mortgages, Swaps) with randomized attributes like issue/maturity dates, amounts, rate types (Fixed, Floating, Hybrid), coupon rates, and payment frequencies. It also assigns `Specific_Features` such as `prepayment_option` for mortgages or `nmd_flag` for non-maturity deposits. This serves as the input banking book for IRRBB analysis.

### 2. Interest Rate Curve Management

*   **`create_baseline_discount_curve(valuation_date, market_rates, tenors_in_months, liquidity_spread_bps)`**:
    Generates a baseline yield curve. It takes market rates at standard tenors (e.g., 1M, 3M, 1Y, 5Y) and interpolates them to create a continuous curve of discount rates for all months up to the maximum tenor. A `liquidity_spread_bps` can be added to reflect funding costs.
*   **`convert_tenor_curve_to_date_curve(tenor_curve_df, valuation_date_for_conversion)`**:
    Converts a tenor-based discount curve (e.g., rate for 12 months) into a date-based curve (e.g., rate for a specific date 12 months from valuation). This is crucial for matching cash flow dates to appropriate discount rates.
*   **`generate_basel_shocked_curve(baseline_curve, scenario_type, shock_magnitudes)`**:
    Applies regulatory-defined interest rate shock scenarios (e.g., Parallel Up, Parallel Down, Steepener, Flattener) to the baseline curve. It takes `shock_magnitudes` (in basis points) for short and long ends of the curve and adjusts the `Rate` column of the curve DataFrame accordingly. This function is central to stress testing.

### 3. Cash Flow Engine

*   **`calculate_cashflows_for_instrument(instrument_data, baseline_curve)`**:
    This is a fundamental function that projects all future cash flows (principal and interest) for a single financial instrument given its characteristics. For floating-rate instruments, it dynamically looks up rates from the provided `baseline_curve`. It accounts for payment frequency and distinguishes between assets and liabilities.

### 4. Behavioral Models

*   **`apply_behavioral_assumptions(cashflow_df, instrument_data, prepayment_rate_annual, nmd_beta, nmd_behavioral_maturity_years)`**:
    Modifies cash flows based on behavioral assumptions, which are critical for realistic IRRBB analysis.
    *   **Mortgage Prepayment**: For instruments flagged with `prepayment_option`, it applies a simplified prepayment model, reducing the final principal and distributing a portion earlier.
    *   **Non-Maturity Deposits (NMDs)**: For deposits flagged as NMDs, it shifts their contractual "on-demand" maturity to a longer, behavioral maturity (e.g., 3 years). NMD Beta, though passed, is primarily applied during PV calculation to adjust the discount rate.

*   **`adjust_behavioral_assumptions_for_shock(cashflow_df, instrument_data, scenario_type, baseline_prepayment_rate, behavioral_shock_adjustment_factor)`**:
    This function applies *changes* to behavioral assumptions specifically due to a shock scenario. For instance, in a "Rates Down" scenario, mortgage prepayment rates might increase, leading to earlier principal repayments. This function adjusts the existing cash flows based on such behavioral shifts.

### 5. Valuation and Risk Metrics

*   **`calculate_present_value_for_cashflows(cashflow_df, discount_curve, valuation_date, instrument_type=None, nmd_beta=0.0)`**:
    Calculates the present value of a set of cash flows using the provided `discount_curve`. It interpolates rates for precise discounting. Importantly, it also applies the `nmd_beta` for NMD liabilities by adjusting their effective discount rate, reflecting their lower sensitivity to market rate changes.
*   **`calculate_eve(pv_assets, pv_liabilities)`**:
    A straightforward calculation of EVE by subtracting the present value of liabilities from the present value of assets.
*   **`map_cashflows_to_basel_buckets(cashflow_df, valuation_date, basel_bucket_definitions)`**:
    Assigns each cash flow to a predefined Basel regulatory time bucket (e.g., 0-1M, 1Y-2Y, 20Y+). This is a prerequisite for Net Gap analysis.
*   **`calculate_net_gap(bucketed_cashflow_df)`**:
    Calculates the net gap for each Basel bucket by summing positive cash flows (assets) and negative cash flows (liabilities, then taking absolute value) and finding their difference.
*   **`calculate_delta_eve(baseline_eve, shocked_eve)`**:
    Computes the change in EVE between a baseline and a shocked scenario.
*   **`report_delta_eve_as_percentage_of_tier1(delta_eve_results, tier1_capital)`**:
    Converts the absolute $\Delta EVE$ results into percentages of the bank's Tier 1 Capital, a key regulatory reporting metric.

### 6. Visualization

*   **`plot_delta_eve_bar_chart(delta_eve_percentages)`**:
    Utilizes `Plotly Graph Objects` to generate an interactive bar chart visualizing the $\Delta EVE$ for each shock scenario as a percentage of Tier 1 Capital. This provides a clear visual summary of the bank's interest rate risk exposure.

<aside class="positive">
By understanding these utility functions, you gain a deep insight into the financial modeling and quantitative risk assessment capabilities of QuLab. Each function plays a specific role in simulating a bank's balance sheet under various interest rate conditions.
</aside>

## Step 1: Portfolio Generation
Duration: 00:05:00

This step focuses on creating the banking book portfolio that will be used for IRRBB analysis. The `portfolio_generation.py` script is responsible for this.

1.  **Navigate to the "Portfolio Generation" page:**
    On the left-hand sidebar of the QuLab application, select "Portfolio Generation" from the "Navigation" dropdown.

2.  **Configure Portfolio Parameters:**
    In the sidebar, you'll find input widgets to customize your synthetic portfolio:
    *   **Number of Instruments**: Determines how many individual loans, deposits, bonds, etc., are generated.
    *   **Tier 1 Capital (TWD)**: Represents the bank's core capital, used for risk percentage calculations.
    *   **Portfolio Start Date**: The earliest possible issue date for instruments.
    *   **Portfolio End Date**: The latest possible maturity date for instruments.
    *   **Valuation Date**: The date as of which all instruments will be valued.

3.  **Generate the Portfolio:**
    Click the "Generate Portfolio" button in the sidebar. The application will use the `generate_synthetic_portfolio` function from `utils.py` to create a new dataset of financial instruments based on your specified parameters.

    ```python
    # Snippet from application_pages/portfolio_generation.py
    # This function is called when the "Generate Portfolio" button is clicked
    taiwan_portfolio_df = generate_synthetic_portfolio(num_instruments, tier1_capital_val, start_date_gen, end_date_gen)
    st.session_state["taiwan_portfolio_df"] = taiwan_portfolio_df
    st.session_state["valuation_date"] = valuation_date
    st.session_state["tier1_capital_val"] = tier1_capital_val
    ```

4.  **Review the Portfolio Overview:**
    Once generated, the main content area will display an "Initial Portfolio Overview," showing the first few rows of the `taiwan_portfolio_df`. You can expand to view the full dataset. Summary statistics (Total Instruments, Total Asset Notional, Total Liability Notional) will also be presented.

    <aside class="positive">
    This generated portfolio is a Pandas DataFrame, containing crucial attributes for each instrument. Take a moment to inspect its columns, such as `Instrument_Type`, `Is_Asset`, `Amount`, `Rate_Type`, `Coupon_Rate`, `Maturity_Date`, and `Specific_Features`. These attributes directly feed into the cash flow generation and valuation processes.
    </aside>

## Step 2: Discount Curve Management
Duration: 00:05:00

This step focuses on understanding and managing the interest rate discount curve, which is essential for present value calculations. The `discount_curve.py` script (assumed) would handle this.

1.  **Navigate to the "Discount Curve" page:**
    Select "Discount Curve" from the "Navigation" dropdown in the sidebar.

2.  **Understand Baseline Curve Generation:**
    The application generates a baseline discount curve based on predefined market rates and tenors in `utils.py`. The `create_baseline_discount_curve` function interpolates these rates to provide a continuous curve. A `liquidity_spread_bps` can be added to simulate funding costs.

    ```python
    # Snippet from utils.py
    @st.cache_data
    def create_baseline_discount_curve(valuation_date, market_rates, tenors_in_months, liquidity_spread_bps):
        # ... logic to create rates_df and interpolate ...
        f_interp = interp1d(rates_for_interp_x, rates_for_interp_y, kind="linear", fill_value="extrapolate")
        all_months = np.arange(0, max_months + 1)
        interpolated_rates = f_interp(all_months)
        baseline_curve_df = pd.DataFrame({
            "Months_to_Maturity": all_months,
            "Rate": interpolated_rates,
        })
        baseline_curve_df["Valuation_Date"] = valuation_date
        return baseline_curve_df
    ```

3.  **Visualize the Curve:**
    A typical implementation of `discount_curve.py` would display the baseline discount curve (e.g., using `plotly`) allowing you to see how rates change across different maturities. This visualization helps in understanding the shape of the yield curve.

    <aside class="negative">
    While the `utils.py` provides the function `convert_tenor_curve_to_date_curve`, the actual UI and user interaction for this page are assumed. In a complete application, you might be able to manually adjust spot rates or apply custom curve shifts here.
    </aside>

## Step 3: IRRBB Simulation
Duration: 00:15:00

This is the core functionality of QuLab, where you simulate the impact of interest rate shocks on the bank's EVE. The `irrbb_simulation.py` script (assumed) orchestrates this process.

### 3.1: Configuring Simulation Parameters

1.  **Navigate to the "IRRBB Simulation" page:**
    Select "IRRBB Simulation" from the "Navigation" dropdown in the sidebar.

2.  **Input Parameters:**
    This page (likely in the sidebar) would allow you to set key parameters for the simulation:
    *   **Prepayment Rate (Annual %)**: The baseline annual prepayment rate for mortgages (e.g., 5% means 0.05).
    *   **Behavioral Shock Adjustment Factor**: How much behavioral models (e.g., prepayment) react to interest rate shocks (e.g., 0.2 means a 20% change in prepayment rate in response to a shock).
    *   **NMD Beta**: The sensitivity of Non-Maturity Deposit rates to market rate changes (e.g., 0.5 means NMD rates move 50% of market rates).
    *   **NMD Behavioral Maturity (Years)**: The effective maturity assigned to NMDs for valuation purposes (e.g., 3 years).

### 3.2: Basel Interest Rate Shock Scenarios

The application provides a set of standard Basel shock scenarios, implemented via the `shock_scenarios` dictionary in `utils.py` and applied by `generate_basel_shocked_curve`. These scenarios are designed to stress-test the banking book.

```python
# Snippet from utils.py
shock_scenarios = {
    "Parallel Up": {"short": 200, "long": 200}, # Example magnitudes in bps
    "Parallel Down": {"short": -200, "long": -200},
    "Steepener": {"short": -50, "long": 100},
    "Flattener": {"short": 100, "long": -50},
    "Short Rate Up": {"short": 200, "long": 0},
    "Short Rate Down": {"short": -200, "long": 0},
}
```

*   **Parallel Up/Down**: The entire yield curve shifts up/down by a constant basis point amount.
*   **Steepener/Flattener**: The short end of the curve moves differently from the long end, causing the curve to steepen or flatten.
*   **Short Rate Up/Down**: Only the short end of the curve experiences a shock, while long rates remain unchanged.

### 3.3: The Simulation Workflow (Deep Dive into `recalculate_cashflows_and_pv_for_scenario`)

When you trigger a simulation (e.g., by selecting scenarios or clicking a "Run Simulation" button on the `irrbb_simulation.py` page), the application executes a complex sequence of calculations for each scenario. This orchestration is primarily handled by the `recalculate_cashflows_and_pv_for_scenario` function.

**Simulation Flow:**
1.  **Generate Baseline EVE:** First, the baseline EVE is calculated. This involves:
    *   Generating cash flows for all instruments using the baseline discount curve (`calculate_cashflows_for_instrument`).
    *   Applying behavioral assumptions (`apply_behavioral_assumptions`) for mortgages (prepayment) and NMDs (behavioral maturity shift).
    *   Calculating the Present Value (PV) of all assets and liabilities using the baseline curve (`calculate_present_value_for_cashflows`).
    *   Finally, computing `EVE_baseline = PV_assets_baseline - PV_liabilities_baseline`.

2.  **For Each Shock Scenario:**
    *   **Generate Shocked Curve**: The `generate_basel_shocked_curve` function creates a new interest rate curve for the specific shock scenario (e.g., "Parallel Up"). This `shocked_curve_date_based` is crucial for subsequent steps.
    *   **Iterate Through Portfolio Instruments**: The function then loops through every instrument in your generated portfolio. For each instrument:
        *   **Generate Baseline Cash Flows (using shocked curve for floating)**: `calculate_cashflows_for_instrument` is called. **Crucially**, if the instrument is floating rate, its cashflows will be initially calculated using the *shocked* curve for its coupon rate.
        *   **Apply General Behavioral Assumptions**: `apply_behavioral_assumptions` is called to implement the baseline prepayment logic for mortgages and the behavioral maturity shift for NMDs.
        *   **Apply Shock-Specific Behavioral Adjustments**: `adjust_behavioral_assumptions_for_shock` is invoked. This is where behavioral models, like mortgage prepayment, are *adjusted* based on the specific `scenario_type`. For instance, a "Rates Down" scenario might increase the prepayment amount.
        *   The final, adjusted cash flows for the instrument under this specific shock are collected.
    *   **Aggregate Cash Flows**: All individual instrument cash flows are concatenated into a single DataFrame for the entire shocked portfolio.
    *   **Calculate Shocked EVE**:
        *   The aggregated cash flows are separated into assets and liabilities.
        *   `calculate_present_value_for_cashflows` is called for both assets and liabilities using the `shocked_curve_date_based`. For liabilities identified as NMDs, the `nmd_beta` is applied to their discount rate within this PV function.
        *   `EVE_shocked = PV_assets_shocked - PV_liabilities_shocked` is calculated.
    *   **Calculate $\Delta EVE$**: `calculate_delta_eve` computes `Delta_EVE = EVE_shocked - EVE_baseline`.

**Visual Flow of a Single Scenario Simulation (`recalculate_cashflows_and_pv_for_scenario`)**:

```
[Start Simulation for Scenario X]
      |
      V
[Generate Shocked Curve for Scenario X]
      |
      V
[For Each Instrument in Portfolio]
      |
      +> [Generate Cashflows (using Shocked Curve for Floating Rates)]
      |          |
      |          V
      |    [Apply Baseline Behavioral Assumptions (Prepayment, NMD Maturity)]
      |          |
      |          V
      |    [Apply Shock-Specific Behavioral Adjustments (e.g., change in Prepayment Rate)]
      |          |
      +-+
      |
      V
[Collect Final Instrument Cashflows under Scenario X]
      |
      V
[Aggregate All Instrument Cashflows for Scenario X]
      |
      V
[Separate into Assets & Liabilities Cashflows]
      |
      V
[Calculate PV of Assets (using Shocked Curve)]
      |
      V
[Calculate PV of Liabilities (using Shocked Curve, applying NMD Beta for Deposits)]
      |
      V
[Calculate EVE_shocked = PV(Assets) - PV(Liabilities)]
      |
      V
[Calculate Delta EVE = EVE_shocked - EVE_baseline]
      |
      V
[Store Delta EVE for Scenario X]
      |
      V
[End of Scenario X Simulation]
