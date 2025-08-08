id: 6891027254d65e6ea0e3f008_user_guide
summary: Lab 5.1 IRRBB Models - Development User Guide
feedback link: https://docs.google.com/forms/d/e/1FAIpQLSfWkOK-in_bMMoHSZfcIvAeO58PAH9wrDqcxnJABHaxiDqhSA/viewform?usp=sf_link
environments: Web
status: Published
# QuLab: Comprehensive Interest Rate Risk in the Banking Book (IRRBB) Engine

## 1. Introduction to IRRBB and the QuLab Application
Duration: 0:05:00

Welcome to the QuLab Codelab, your guide to understanding and simulating Interest Rate Risk in the Banking Book (IRRBB)!

Interest Rate Risk in the Banking Book (IRRBB) refers to the risk to a bank's capital and earnings arising from adverse movements in interest rates that affect its banking book positions. Unlike trading book positions, which are held for short-term trading and are marked to market frequently, banking book positions (like loans, deposits, and bonds) are typically held to maturity. Changes in interest rates can significantly impact the present value of these positions, directly affecting a bank's Economic Value of Equity (EVE).

The **Basel Committee on Banking Supervision** provides a framework for managing and measuring IRRBB, emphasizing the importance of assessing the impact of interest rate movements on both earnings and economic value. This application focuses on the Economic Value of Equity (EVE) perspective, which is a long-term measure of a bank's capital.

This QuLab application provides a full-revaluation framework to analyze the impact of interest rate changes on a bank's EVE. It allows you to simulate a synthetic banking book portfolio, generate cash flows, apply various Basel interest rate shock scenarios, and quantify the resulting $\Delta EVE$ (change in EVE).

### Learning Goals

Upon completing this codelab, you will be able to:
*   Assemble a banking-book positions dataset that captures interest-sensitive assets, liabilities, and (optionally) simple hedges.
*   Generate synthetic cash-flow data for those positions, respecting product features and behavioral assumptions.
*   Build a full-revaluation IRRBB engine that computes baseline present values, allocates cash flows into regulatory time buckets, and estimates $\Delta EVE$ under the Basel six-scenario shock set.
*   Report $\Delta EVE$ as a percentage of Tier 1 capital and interpret the risk signal of each scenario.

### Mathematical Foundations for EVE

The Present Value (PV) of a series of cash flows is the sum of the present values of each individual cash flow. For a single cash flow $CF_t$ received at time $t$, discounted at a rate $r_t$:
$$ PV(CF_t) = \frac{CF_t}{(1 + r_t)^{t}} $$
For a series of cash flows $CF_1, CF_2, \ldots, CF_M$ occurring at times $t_1, t_2, \ldots, t_M$:
$$ PV = \sum_{k=1}^{M} \frac{CF_k}{(1 + r_{t_k})^{t_k}} $$
For EVE calculation, the cash flows will be discounted using a risk-free yield curve plus an appropriate liquidity spread; commercial margins are excluded.

EVE is defined as the present value of all banking book assets minus the present value of all banking book liabilities and off-balance sheet items:
$$ EVE_{\text{baseline}} = \sum_{i=1}^{N_A} PV(CF_{A,i}) - \sum_{j=1}^{N_L} PV(CF_{L,j}) $$

$\Delta EVE$ measures the change in a bank's EVE due to an interest rate shock:
$$ \Delta EVE = EVE_{\text{shocked}} - EVE_{\text{baseline}} $$

$\Delta EVE$ will be reported as a percentage of Tier 1 capital, allowing for a standardized interpretation of the risk signal:
$$ \Delta EVE (\% \text{ Tier 1 Capital}) = \frac{\Delta EVE}{\text{Tier 1 Capital}} \times 100\% $$

The net gap for each time bucket represents the difference between total cash inflows (from assets) and total cash outflows (from liabilities and derivatives) within that bucket:
$$ Net\ Gap_{\text{bucket } k} = \sum_{\text{assets in bucket } k} CF_{\text{in}} - \sum_{\text{liabilities in bucket } k} CF_{\text{out}} $$

The application is structured into three main pages, which you can navigate using the sidebar on the left:
*   **Portfolio Generation**: Where you set up your synthetic banking book.
*   **Cash Flow & Gap Analysis**: Where cash flows are projected, behavioral assumptions are applied, and the initial EVE and net gap are calculated.
*   **IRRBB Simulation Results**: Where the full interest rate shock scenarios are applied and $\Delta EVE$ is determined and presented.

Let's begin by generating our banking book portfolio.

## 2. Generating Your Banking Book Portfolio
Duration: 0:03:00

In this step, you will generate a synthetic banking book portfolio. This portfolio simulates the assets and liabilities a typical bank holds, such as loans, deposits, and bonds. Each instrument in the portfolio will have distinct characteristics crucial for IRRBB analysis.

1.  **Navigate to the "Portfolio Generation" page**:
    In the sidebar, select "Portfolio Generation" from the "Navigation" dropdown.

2.  **Adjust Portfolio Generation Parameters**:
    On the left sidebar, locate the "Portfolio Generation Parameters" expander. Here you can configure the size and financial context of your synthetic banking book:
    *   **Number of Instruments**: This determines how many individual loans, deposits, or bonds will be created in your portfolio. A larger number provides a more diverse and realistic portfolio.
    *   **Tier 1 Capital (TWD)**: This represents the bank's core capital. It's essential for later reporting $\Delta EVE$ as a percentage, which helps standardize risk assessment across banks of different sizes.
    *   **Portfolio Start Date**: The effective date from which the instruments in your portfolio are considered active.
    *   **Portfolio End Date**: The latest possible maturity date for any instrument within the generated portfolio.

    <aside class="positive">
    <b>Tip:</b> While you can change these parameters, starting with the default values is recommended for your first run to get familiar with the application.
    </aside>

3.  **Generate the Portfolio**:
    As soon as you adjust the parameters, or if you navigate to this page for the first time, the application automatically generates the synthetic portfolio. You will see a success message: "Synthetic Banking Book Portfolio Generated!".

4.  **Review the Generated Portfolio**:
    Below the parameters, you will see a subheader "Generated Synthetic Banking Book Portfolio" followed by a table showing the first 5 rows of your portfolio. This table gives you a glimpse into the types of instruments generated, including their:
    *   `instrument_id`: A unique identifier for each instrument.
    *   `category`: Loan, Deposit, or Bond.
    *   `balance`: The notional amount of the instrument.
    *   `rate_type`: Whether the instrument has a 'Fixed' or 'Floating' interest rate.
    *   `maturity_date`: When the instrument's principal is due.
    *   `next_repricing_date`: For floating-rate instruments, when the interest rate will next reset.
    *   `is_core_NMD`: Indicates if a deposit is considered a "core Non-Maturity Deposit" (NMD), which has special behavioral assumptions.

    You will also see a summary of the total number of instruments and the total portfolio balance.

5.  **Download the Portfolio (Optional)**:
    You have the option to download the full generated portfolio as a CSV file for your own analysis.

Now that we have our banking book portfolio, let's move on to projecting its cash flows and analyzing the interest rate gap.

## 3. Understanding Cash Flow and Gap Analysis
Duration: 0:08:00

This is a crucial step where the application projects the future cash flows of your portfolio and prepares for IRRBB analysis. It involves several key concepts:

1.  **Navigate to the "Cash Flow & Gap Analysis" page**:
    In the sidebar, select "Cash Flow & Gap Analysis" from the "Navigation" dropdown.

2.  **Understand the Concepts and Parameters**:
    This page introduces the following important concepts and parameters:

    *   **Discount Curve**: This curve represents the set of interest rates used to calculate the present value of future cash flows. It's built from market rates (risk-free rates) and adjusted by a **Liquidity Spread (bps)**. This spread accounts for the premium required by investors for holding less liquid assets.
    *   **Cash Flow Projection**: For each instrument in your portfolio (loans, deposits, bonds), the application projects future interest and principal payments based on their type, balance, current rate, payment frequency, and maturity date.
    *   **Behavioral Adjustments**: Real-world financial products often exhibit behaviors that deviate from contractual terms. This application models two key behavioral assumptions:
        *   **Mortgage Prepayment**: Borrowers might repay their mortgages earlier than contractually agreed, especially if interest rates fall. The **Mortgage Prepayment Rate (Annual)** dictates how much principal is assumed to be repaid early each year.
        *   **Non-Maturity Deposits (NMDs)**: These are deposits like checking or savings accounts that don't have a fixed maturity date. While they are contractually callable on demand, a stable portion often remains with the bank for extended periods. The **NMD Beta** represents the proportion of NMDs considered "stable", and the **NMD Behavioral Maturity (Years)** assigns an assumed average maturity to this stable portion. This reflects that a significant portion of these deposits behaves like long-term funding.
    *   **Behavioral Shock Adjustment Factor**: This parameter indicates how much the behavioral assumptions (e.g., prepayment rates) might change under stress interest rate scenarios. For example, if rates go up, prepayment rates might decrease.
    *   **Net Gap**: This is a key measure in IRRBB, representing the difference between interest-sensitive assets and liabilities maturing or repricing within specific time buckets. A positive gap means more assets are repricing or maturing in that bucket (asset sensitivity), while a negative gap means more liabilities are (liability sensitivity). Analyzing the net gap across different time buckets helps identify concentrations of interest rate risk.

3.  **Set Model Parameters**:
    In the sidebar, within the "Model Parameters" expander, you can adjust the values for:
    *   `Liquidity Spread (bps)`
    *   `Mortgage Prepayment Rate (Annual)`
    *   `NMD Beta`
    *   `NMD Behavioral Maturity (Years)`
    *   `Behavioral Shock Adjustment Factor`

    <aside class="positive">
    <b>Tip:</b> Experiment with these parameters after your first run. For instance, increasing the Mortgage Prepayment Rate or NMD Beta can significantly alter the cash flow profiles and EVE.
    </aside>

4.  **Run Cash Flow & Gap Analysis**:
    Click the "Run Cash Flow & Gap Analysis" button. The application will perform the following computations:
    *   Create the **Baseline Discount Curve** using the market rates and your specified liquidity spread.
    *   **Generate All Cash Flows** for every instrument, applying the behavioral assumptions.
    *   **Map Cash Flows to Basel Buckets**: Allocate each cash flow into predefined regulatory time buckets (e.g., 0-1 month, 1-3 months, 1-2 years, etc.).
    *   Calculate the **Baseline EVE**: Compute the Present Value of all assets and liabilities using the baseline discount curve and then calculate the initial EVE.
    *   Calculate the **Net Gap Table**: Summarize the net cash flow (assets - liabilities) for each time bucket.

    You will see success messages as each step completes.

5.  **Review the Results**:
    Once the analysis is complete, scroll down to the "Results" section:
    *   **Baseline Discount Curve**: A table showing the tenor (time to maturity in months) and the corresponding discount rate. This is the curve used to value all baseline cash flows.
    *   **First 5 Rows of Cash Flows with Basel Buckets**: A sample of the generated cash flows, now including the `basel_bucket` they fall into.
    *   **Net Gap Table**: This table is crucial for understanding interest rate risk. It shows the sum of asset cash flows, liability cash flows, and the net gap (Assets CF + Liabilities CF, where liabilities are negative) for each Basel bucket. You can download this table as a Parquet file.
    *   **Baseline EVE**: The calculated Economic Value of Equity for your portfolio under the current market conditions (before any shocks).

    <aside class="negative">
    <b>Important:</b> Ensure that the "Cash Flow & Gap Analysis" runs successfully before proceeding to the next step, as its outputs are prerequisites for the simulation. If you see warnings about no cash flows generated, revisit your portfolio parameters.
    </aside>

You have now set up your portfolio, projected its cash flows, and established a baseline for your IRRBB analysis. The next step is to simulate interest rate shocks and measure their impact.

## 4. Simulating Interest Rate Shocks and Analyzing $\Delta EVE$
Duration: 0:07:00

This is the core of the IRRBB analysis, where we stress-test the banking book against predefined interest rate scenarios to understand the potential impact on Economic Value of Equity ($\Delta EVE$).

1.  **Navigate to the "IRRBB Simulation Results" page**:
    In the sidebar, select "IRRBB Simulation Results" from the "Navigation" dropdown.

    <aside class="negative">
    <b>Important:</b> If you haven't completed the "Portfolio Generation" and "Cash Flow & Gap Analysis" steps, you will see warning messages prompting you to do so. This page relies on the generated portfolio, baseline discount curve, and baseline EVE from the previous steps.
    </aside>

2.  **Understand the Simulation Concepts**:

    *   **Interest Rate Shock Scenarios**: The Basel framework prescribes a standard set of six interest rate shock scenarios to capture various forms of interest rate risk. These include:
        *   **Parallel Up**: All interest rates across the yield curve increase by a uniform amount (e.g., +200 bps).
        *   **Parallel Down**: All interest rates decrease by a uniform amount (e.g., -200 bps).
        *   **Steepener**: Short-term rates decrease, while long-term rates increase, leading to a steeper yield curve.
        *   **Flattener**: Short-term rates increase, while long-term rates decrease, leading to a flatter yield curve.
        *   **Short-Up**: Only short-term rates increase, with long-term rates remaining unchanged.
        *   **Short-Down**: Only short-term rates decrease, with long-term rates remaining unchanged.

    *   **Revaluation under Shock**: For each of these scenarios, the application performs a full revaluation:
        *   A **shocked discount curve** is generated based on the scenario's prescribed rate changes.
        *   For **floating-rate instruments**, their future cash flows are repriced using the new shocked curve.
        *   **Behavioral assumptions** (like the mortgage prepayment rate) are adjusted based on the `Behavioral Shock Adjustment Factor` and the direction of the interest rate change (e.g., prepayment may decrease when rates go up).
        *   The **Present Value of all assets and liabilities is recalculated** using the shocked cash flows and the shocked discount curve, resulting in a new **Shocked EVE**.

    *   **$\Delta EVE$ Calculation**: The change in EVE is then calculated as the difference between the `Shocked EVE` and the `Baseline EVE`.
        $\Delta EVE = EVE_{\text{shocked}} - EVE_{\text{baseline}}$
        A negative $\Delta EVE$ indicates a loss in economic value under that scenario, signaling a risk exposure.

    *   **Reporting as % of Tier 1 Capital**: To provide a standardized measure of risk that can be compared across banks, $\Delta EVE$ is reported as a percentage of the bank's Tier 1 Capital. This helps assess the materiality of the potential impact relative to the bank's core capital.

3.  **Run IRRBB Simulation**:
    Click the "Run IRRBB Simulation" button. A progress bar will appear, showing the simulation processing each of the six Basel scenarios. This might take a moment depending on the number of instruments in your portfolio.

4.  **Review Simulation Results**:
    Once the simulation is complete, you will see a success message and the results will be displayed:
    *   **Baseline EVE**: Your reference EVE value.
    *   **Total Instruments Analyzed** and **Scenarios Analyzed**: Summary information.
    *   **Delta EVE Report (% of Tier 1 Capital)**: This table presents the absolute $\Delta EVE$ in TWD and, critically, the $\Delta EVE$ as a percentage of Tier 1 Capital for each scenario.
        <aside class="positive">
        <b>Interpretation:</b> A significant negative percentage for any scenario indicates a material exposure to that particular interest rate shock. For example, a large negative $\Delta EVE$ under "Parallel Up" suggests the bank's economic value is highly sensitive to rising interest rates.
        </aside>
    *   **Bar Chart**: A visual representation of the $\Delta EVE$ results, making it easy to compare the impact of different scenarios at a glance.
    *   **Download Model Artifact**: You can download a `.pkl` file containing the key results and parameters of this simulation for record-keeping or further analysis. This is important for audit trails and internal reporting.

You have successfully performed a comprehensive IRRBB analysis using the QuLab application!

## 5. Conclusion and Next Steps
Duration: 0:02:00

Congratulations! You have successfully navigated the QuLab application to perform a full-revaluation Interest Rate Risk in the Banking Book (IRRBB) analysis.

Throughout this codelab, you have learned to:
*   Generate a synthetic banking book portfolio with various instrument types.
*   Understand the process of cash flow projection, including behavioral adjustments for products like mortgages and Non-Maturity Deposits (NMDs).
*   Calculate a baseline Economic Value of Equity (EVE) and perform a Net Gap analysis to identify interest rate sensitivities across different time buckets.
*   Simulate the impact of standardized Basel interest rate shock scenarios on your portfolio.
*   Quantify and interpret the change in EVE ($\Delta EVE$), reporting it as a percentage of Tier 1 capital, which is crucial for assessing risk materiality.
*   Visualize and export your IRRBB analysis results.

This application provides a robust foundation for understanding the mechanics of IRRBB and the application of Basel guidelines in a practical setting. The concepts covered, such as present value, discounting, cash flow modeling, behavioral assumptions, and scenario analysis, are fundamental to financial risk management.

### Further Exploration:
*   **Experiment with Parameters**: Go back to "Portfolio Generation" and "Cash Flow & Gap Analysis" to change the number of instruments, Tier 1 Capital, liquidity spread, or behavioral rates. Observe how these changes affect the baseline EVE, net gap, and especially the $\Delta EVE$ under different scenarios.
*   **Deep Dive into Basel Guidelines**: Consult the official Basel Committee documents on IRRBB (e.g., BCBS 368) to gain a deeper understanding of the regulatory expectations and other aspects like Earnings at Risk (EAR).
*   **Real-World Data**: In a production environment, you would use actual bank portfolio data, which would be far more complex and require sophisticated data handling and validation.
*   **Advanced Models**: Explore how more complex behavioral models (e.g., dynamic prepayment models linked to interest rate changes), embedded options (like caps/floors), and hedging strategies (e.g., interest rate swaps) could be incorporated into such an engine.

Thank you for completing this QuLab codelab! We hope this experience has provided you with valuable insights into Interest Rate Risk in the Banking Book.
