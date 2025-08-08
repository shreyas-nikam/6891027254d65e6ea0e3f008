id: 6891027254d65e6ea0e3f008_user_guide
summary: Lab 5.1 IRRBB Models - Development User Guide
feedback link: https://docs.google.com/forms/d/e/1FAIpQLSfWkOK-in_bMMoHSZfcIvAeO58PAH9wrDqcxnJABHaxiDqhSA/viewform?usp=sf_link
environments: Web
status: Published
# Understanding Interest Rate Risk in the Banking Book (IRRBB) with QuLab

## Introduction to IRRBB and the QuLab Application
Duration: 0:05

Welcome to this codelab! In the world of finance, managing risk is paramount, and for banks, one of the most critical risks is **Interest Rate Risk in the Banking Book (IRRBB)**. This risk arises from the impact of adverse movements in interest rates on a bank's non-trading positions (assets and liabilities held with the intention of being held to maturity or for liquidity purposes).

The **QuLab** application provides an interactive environment to explore IRRBB, specifically focusing on the **Economic Value of Equity (EVE)** framework. EVE is a key metric that gives a static, long-term view of how changes in interest rates affect the present value of a bank's expected future cash flows.

Let's break down the core concepts you'll interact with in this application:

*   **Economic Value of Equity (EVE):** At its heart, EVE represents the net present value of all future cash flows from a bank's assets, liabilities, and off-balance sheet items. It is calculated as the Present Value (PV) of assets minus the Present Value of liabilities:

    $$ EVE_{\text{baseline}} = \sum_{i=1}^{N_A} PV(CF_{A,i}) - \sum_{j=1}^{N_L} PV(CF_{L,j}) $$

*   **Present Value (PV) Calculation:** The value today of a future cash flow is found by discounting it using an appropriate interest rate. The formula for discounting a single cash flow ($CF_t$) at time $t$ is:

    $$ PV(CF_t) = \frac{CF_t}{(1 + r_t)^{t}} $$

    For a series of cash flows, the total Present Value is the sum of the present values of all individual cash flows.
    <aside class="positive">
    <b>Important Note on Discounting:</b> The discount rates used in EVE calculations typically reflect risk-free rates plus a liquidity spread. They are explicitly designed to *exclude* commercial margins, as EVE focuses solely on the impact of interest rate changes on the underlying value, not on business profitability.
    </aside>

*   **Change in Economic Value of Equity ($\Delta EVE$):** This measures how sensitive a bank's economic value is to changes in interest rates. It's simply the difference between the EVE under a "shocked" interest rate scenario and the initial baseline EVE:

    $$ \Delta EVE = EVE_{\text{shocked}} - EVE_{\text{baseline}} $$

    To standardize reporting and compare banks, $\Delta EVE$ is often expressed as a percentage of the bank's Tier 1 Capital, which is a key measure of a bank's financial strength:

    $$ \Delta EVE (\% \text{ Tier 1 Capital}) = \frac{\Delta EVE}{\text{Tier 1 Capital}} \times 100\% $$

*   **Cash Flow Generation and Behavioral Assumptions:** Accurately projecting cash flows is crucial. This application incorporates:
    *   **Fixed vs. Floating Rates:** Distinguishing between instruments with set interest payments and those that reprice based on market benchmarks.
    *   **Mortgage Prepayment:** Modeling how homeowners might repay their mortgages early, affecting future cash inflows.
    *   **Non-Maturity Deposit (NMD) Beta ($\beta$):** Modeling how the interest rates on deposits without a contractual maturity (like checking accounts) respond to changes in market rates.

*   **Basel Interest Rate Shock Scenarios:** Regulatory bodies, like Basel, prescribe specific hypothetical interest rate changes to test a bank's resilience. The application simulates six common scenarios: Parallel Up, Parallel Down, Steepener, Flattener, Short-Term Rate Up, and Short-Term Rate Down.

*   **Net Gap Analysis:** This offers a complementary view to EVE, focusing on the difference between interest-sensitive assets and liabilities repricing or maturing within defined time buckets. It provides insights into short-to-medium term liquidity and earnings sensitivity.

    $$ Net\ Gap_{\text{bucket } k} = \sum_{\text{assets in bucket } k} CF_{\text{in}} - \sum_{\text{liabilities in bucket } k} CF_{\text{out}} $$

This application will allow you to generate a synthetic banking portfolio, apply these concepts, and visualize the impact of various parameters and interest rate shocks on a bank's IRRBB profile.

## Navigating the QuLab Application
Duration: 0:02

The QuLab application is built with Streamlit, which organizes content neatly using a sidebar for navigation.

1.  **Sidebar:** On the left side of your screen, you'll see a sidebar labeled "Navigation". This is where you switch between different sections of the application.
2.  **Navigation Options:** The sidebar offers three main pages:
    *   **Portfolio Generation:** This page provides an introduction to the lab and outlines what you can do with the application.
    *   **IRRBB Analysis:** This is the core simulation page where you'll input parameters, run the IRRBB calculations, and view the results.
    *   **About:** This page provides general information about the application, its purpose, and the technologies used.

<aside class="positive">
To proceed with the main simulation, please select **"IRRBB Analysis"** from the navigation sidebar.
</aside>

## Understanding the Portfolio Generation Introduction
Duration: 0:03

When you first open the application or select "Portfolio Generation" from the sidebar, you'll see an introductory page.

This page, titled "Introduction to Lab 5.1: IRRBB Models - Development", serves as a welcome and explains the key capabilities of the application. It highlights that you can:

*   Generate a synthetic banking portfolio.
*   Project cash flows, incorporating behavioral assumptions.
*   Calculate baseline EVE and Net Gap.
*   Simulate various interest rate shock scenarios.
*   Report the change in EVE ($\Delta EVE$) as a percentage of Tier 1 Capital.

The instructions on this page will guide you to the "IRRBB Analysis" page for running the actual simulations, which is what we will do next.

## Setting Up and Running the IRRBB Simulation
Duration: 0:10

Now, let's dive into the core functionality of the QuLab application on the "IRRBB Analysis" page. If you haven't already, please select **"IRRBB Analysis"** from the left-hand navigation sidebar.

On this page, you'll find various input parameters in the sidebar on the left. These parameters allow you to customize your synthetic banking portfolio and the conditions for the IRRBB simulation.

### Portfolio Generation Parameters:

*   **Number of Instruments:** Use the slider to define how many synthetic financial instruments (like mortgages, corporate loans, fixed deposits, etc.) will be generated for your banking portfolio. More instruments will provide a more diverse portfolio but may increase calculation time.
    *   *Try setting this to 25 for a quick run.*
*   **Tier 1 Capital (TWD):** Input the bank's Tier 1 Capital amount. This value is crucial as the $\Delta EVE$ results are reported as a percentage of this capital, which is a key regulatory metric.
    *   *A default of 1,000,000,000 TWD is a good starting point.*
*   **Portfolio Start Date & End Date:** These dates define the range within which the issue and maturity dates for your synthetic instruments will be randomly generated.
    *   *The defaults (e.g., 2023-01-01 to 2050-12-31) are usually fine.*
*   **Valuation Date:** This is the "today" date for your calculations. All cash flows will be discounted back to this date to calculate their present value.
    *   *This will default to the current date.*

### Discount Curve Parameters:

*   **Liquidity Spread (bps):** This slider allows you to add an extra spread (in basis points) to the underlying risk-free market interest rate curve. This adjusted curve is then used to discount all future cash flows.
    *   *Start with 10 bps (0.10%).*

### Behavioral Assumption Parameters:

These parameters are essential for accurately modeling instruments that don't have fixed contractual maturities or where customer behavior impacts cash flows.

*   **Annual Mortgage Prepayment Rate:** This rate simulates how much of outstanding mortgage principal might be paid back early each year. When interest rates fall, borrowers might refinance, leading to higher prepayments.
    *   *A default of 5% (0.05) is provided.*
*   **NMD Beta:** Non-Maturity Deposits (NMDs), like checking or savings accounts, don't have a fixed maturity. Their interest rates often don't move 1-for-1 with market rates. The NMD Beta (between 0 and 1) represents how sensitive the NMD rate is to changes in market interest rates. A beta of 1 means it moves perfectly with the market, 0 means it doesn't move at all.
    *   *A default of 0.5 (50%) is provided.*
*   **NMD Behavioral Maturity (Years):** Since NMDs have no contractual maturity, a behavioral maturity is assigned to them for EVE modeling. This is the assumed average life of these deposits.
    *   *A default of 3.0 years is common.*
*   **Behavioral Shock Adjustment Factor:** This factor determines how much the behavioral rates (like prepayment rate and NMD beta) themselves change under interest rate shock scenarios. For example, if interest rates rise, mortgage prepayments might decrease, and NMD betas might increase.
    *   *A default of 0.10 (10%) is provided.*

### Running the Simulation:

After adjusting your desired parameters, click the **"Run IRRBB Simulation"** button in the sidebar.

<aside class="positive">
You'll see progress bars indicating that the application is generating the portfolio, creating cash flows, and running the stress scenarios. Please wait for the "Simulation complete!" message to appear.
</aside>

## Interpreting the Simulation Results
Duration: 0:15

Once the simulation completes, the main content area of the "IRRBB Analysis" page will populate with several sections displaying the results. Let's go through each one:

### 1. Initial Portfolio Overview

This section displays a preview of the synthetic banking portfolio generated based on your parameters. You'll see instrument IDs, product types (e.g., Mortgage, Fixed Deposit), notional amounts, issue/maturity dates, and whether they are fixed or floating rate.

<aside class="positive">
You can click "View Full Portfolio Details" to expand and see the entire generated dataset.
</aside>

### 2. Baseline Discount Curve

This table shows the calculated baseline discount curve. This curve is derived from a set of standard market rates (e.g., government bond yields) to which your specified "Liquidity Spread" has been added. This curve is then used to calculate the present value of all future cash flows for your portfolio under the baseline (no shock) scenario.

<aside class="positive">
A corresponding "Baseline Date Curve Details" expander shows the specific dates mapped from the tenors for precise discounting.
</aside>

### 3. Baseline Economic Value of Equity (EVE)

This section presents the initial EVE of your portfolio before any interest rate shocks are applied.

*   **Baseline EVE:** The overall net present value of the portfolio.
*   **PV of Assets (Baseline):** The sum of the present values of all cash inflows from assets.
*   **PV of Liabilities (Baseline):** The sum of the present values of all cash outflows from liabilities (note: this value will typically be negative as it represents outflows).

The **Baseline EVE** is simply the PV of Assets minus the absolute value of PV of Liabilities (or PV Assets + PV Liabilities since liabilities are usually negative). This number represents the economic value of the bank as of the valuation date, given the current interest rate environment.

### 4. Net Gap Analysis

This table and accompanying bar chart provide a different perspective on interest rate risk, focusing on cash flow mismatches across defined time buckets (e.g., 0-1M, 1M-3M, etc.).

*   **Bucket:** The time horizon (e.g., 0-1 month, 1-3 months).
*   **Total Inflows:** Sum of all cash inflows (from assets) expected within that bucket.
*   **Total Outflows:** Sum of all cash outflows (from liabilities) expected within that bucket.
*   **Net Gap:** Total Inflows - Total Outflows.

<aside class="positive">
<b>Interpreting Net Gap:</b>
A **positive Net Gap** in a bucket means you have more interest-sensitive assets maturing or repricing than liabilities, making your bank **asset-sensitive** to interest rate changes in that bucket. If rates rise, your earnings from assets might increase more than your cost of liabilities.
A **negative Net Gap** means you have more interest-sensitive liabilities maturing or repricing than assets, making your bank **liability-sensitive**. If rates rise, your cost of liabilities might increase more than your earnings from assets.
</aside>

The bar chart visually represents the net gap across these buckets, making it easy to identify periods of significant interest rate sensitivity.

### 5. Delta EVE Report (% of Tier 1 Capital)

This is a critical section that summarizes the impact of the Basel interest rate shock scenarios on the bank's economic value.

*   **Scenario:** Each of the six prescribed Basel interest rate shock scenarios.
*   **Delta_EVE_Value:** The absolute change in EVE (EVE_shocked - EVE_baseline) for that scenario.
*   **Percentage_of_Tier1_Capital:** The $\Delta EVE$ expressed as a percentage of the Tier 1 Capital you entered in the sidebar. This is the primary regulatory reporting metric.

The accompanying bar chart provides a clear visual comparison of the $\Delta EVE$ impact across scenarios.

<aside class="negative">
<b>Interpretation of $\Delta EVE$ Chart:</b>
A <b>negative $\Delta EVE$</b> indicates a decrease in the bank's economic value under that specific interest rate shock scenario. This is an adverse outcome. For example, a "Parallel Up" shock causing a negative $\Delta EVE$ means the bank's long-term value decreases when interest rates uniformly rise.
A <b>positive $\Delta EVE$</b> indicates an increase in economic value under that scenario.
Regulators carefully monitor negative $\Delta EVE$ figures, often setting limits (e.g., maximum 15% or 20% of Tier 1 Capital) to ensure banks can withstand severe interest rate movements.
</aside>

<aside class="positive">
<b>Experimentation:</b> We encourage you to go back to the sidebar and change parameters, especially the "Number of Instruments," "Liquidity Spread," and the "Behavioral Assumption Parameters." Observe how these changes affect the baseline EVE, the Net Gap, and most importantly, the $\Delta EVE$ results under various shock scenarios. This hands-on experimentation will deepen your understanding of IRRBB.
</aside>

## Learning More About the Application
Duration: 0:01

Finally, if you're interested in learning more about the QuLab application itself, its purpose, or the technologies that power it, navigate to the **"About"** page in the sidebar.

This page provides a summary of the application's key features, reiterates its educational purpose for understanding IRRBB, and lists the underlying technologies used (Streamlit, Pandas, NumPy, SciPy, Plotly). It also includes contact information for Quant University for further inquiries.

This concludes your guided tour of the QuLab IRRBB simulation application. Experiment freely and enhance your understanding of this critical banking risk!
