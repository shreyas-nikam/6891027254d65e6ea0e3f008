id: 6891027254d65e6ea0e3f008_user_guide
summary: Lab 5.1 IRRBB Models - Development User Guide
feedback link: https://docs.google.com/forms/d/e/1FAIpQLSfWkOK-in_bMMoHSZfcIvAeO58PAH9wrDqcxnJABHaxiDqhSA/viewform?usp=sf_link
environments: Web
status: Published
# Understanding Interest Rate Risk in the Banking Book (IRRBB) with QuLab

## Introduction to IRRBB and Economic Value of Equity (EVE)
Duration: 0:05

Welcome to QuLab! In this lab, you will explore the critical concept of Interest Rate Risk in the Banking Book (IRRBB), focusing specifically on its impact on a bank's Economic Value of Equity (EVE). This application provides a hands-on simulation tool to understand how changes in interest rates can affect a bank's financial stability and value.

<aside class="positive">
Understanding IRRBB is crucial for banks as it directly influences their profitability, capital adequacy, and overall financial health. Regulators globally emphasize robust IRRBB management and reporting.
</aside>

**Key Concepts Explained in This Application:**

*   **IRRBB:** Interest Rate Risk in the Banking Book - This is the risk that a bank's earnings and capital will be negatively affected by adverse movements in interest rates. It arises from mismatches in the repricing or maturity of assets, liabilities, and off-balance sheet items.
*   **EVE (Economic Value of Equity):** This metric represents the long-term impact of interest rate changes on a bank's net worth. It is calculated as the difference between the present value of a bank's assets and the present value of its liabilities. It gives a comprehensive view of the bank's capital from an economic perspective.
*   **ΔEVE:** The change in EVE. This is the primary output of an IRRBB simulation, showing how EVE shifts from a baseline scenario under various interest rate shocks. Regulators use ΔEVE, especially as a percentage of Tier 1 Capital, to assess a bank's vulnerability to interest rate risk.
*   **Net Gap:** A simpler, time-bucketed measure of interest rate risk. It represents the difference between interest-rate-sensitive assets and liabilities within specific time frames. A positive gap means more assets are repricing or maturing than liabilities in that period, indicating sensitivity to rate increases.

**Mathematical Definitions:**

The application performs calculations based on these fundamental financial formulas:

*   **Economic Value of Equity (EVE):**
    $$ EVE_{\text{baseline}} = \sum_{i=1}^{N_A} PV(CF_{A,i}) - \sum_{j=1}^{N_L} PV(CF_{L,j}) $$
    Where:
    *   $N_A$ is the number of assets.
    *   $N_L$ is the number of liabilities.
    *   $PV(CF_{A,i})$ is the present value of the cash flows of asset $i$.
    *   $PV(CF_{L,j})$ is the present value of the cash flows of liability $j$.

*   **Present Value (PV) Calculation:**
    The present value of a single cash flow $CF_t$ received at time $t$ is calculated as:
    $$ PV(CF_t) = \frac{CF_t}{(1 + r_t)^{t}} $$
    Or, for a series of cash flows:
    $$ PV = \sum_{k=1}^{M} \frac{CF_k}{(1 + r_{t_k})^{t_k}} $$
    Where:
    *   $CF_t$ is the cash flow at time t.
    *   $r_t$ is the discount rate for time t (derived from the discount curve).
    *   $r_{t_k}$ is the discount rate for time $t_k$.

*   **Change in Economic Value of Equity (ΔEVE):**
    $$ \Delta EVE = EVE_{\text{shocked}} - EVE_{\text{baseline}} $$
    To assess regulatory impact, ΔEVE is often reported relative to a bank's capital:
    $$ \Delta EVE (\% \text{ Tier 1 Capital}) = \frac{\Delta EVE}{\text{Tier 1 Capital}} \times 100\% $$

This codelab will guide you through generating a synthetic banking portfolio, setting up discount curves, simulating interest rate shocks, and analyzing the resulting impact on EVE and Net Gap.

## Generating Your Banking Book Portfolio
Duration: 0:07

The first step in simulating IRRBB is to define your bank's current portfolio of assets and liabilities. QuLab provides a "Portfolio Generation" page to create a synthetic, yet realistic, banking book.

1.  **Navigate to the "Portfolio Generation" page:**
    *   In the sidebar navigation, select "Portfolio Generation".

2.  **Configure Portfolio Parameters:**
    *   On the sidebar, you'll see several input fields:
        *   **Number of Instruments:** Use the slider to choose how many financial instruments (e.g., loans, deposits, bonds) to generate. More instruments will provide a more detailed portfolio but may increase calculation time slightly.
        *   **Tier 1 Capital (TWD):** Enter the bank's Tier 1 Capital. This value is crucial for reporting ΔEVE as a percentage of capital, a key regulatory metric.
        *   **Portfolio Start Date:** Select the earliest possible issue date for instruments in your portfolio.
        *   **Portfolio End Date:** Select the latest possible maturity date for instruments.
        *   **Valuation Date:** This is the date as of which all calculations (cash flow present values, EVE) will be performed. Typically, this is today's date or a recent reporting date.

3.  **Generate the Portfolio:**
    *   After setting your desired parameters, click the "Generate Portfolio" button in the sidebar.
    *   A spinner will appear, indicating that the application is creating the synthetic instruments. Once complete, you'll see a success message.

4.  **Review the Generated Portfolio:**
    *   The main section of the page will display an "Initial Portfolio Overview" showing the first few rows of your generated data.
    *   Click "View Full Portfolio Data" to inspect the entire dataset, including instrument IDs, types (Loan, Deposit, Bond, Mortgage, Swap), whether it's an asset or liability, issue and maturity dates, amounts, rate types (Fixed, Floating, Hybrid), coupon rates, payment frequencies, and specific features (like prepayment options for mortgages or NMD flags for deposits).
    *   "Portfolio Summary Statistics" provides aggregate metrics such as the total number of instruments and the total notional amounts for assets and liabilities.

<aside class="positive">
This generated portfolio serves as the baseline for all subsequent interest rate risk analyses. The mix of fixed vs. floating rates, and the maturity profiles of these instruments, will largely determine your bank's exposure to interest rate risk.
</aside>

## Understanding and Adjusting the Discount Curve
Duration: 0:08

The discount curve (also known as the yield curve) is fundamental to financial valuation. It provides the discount rates needed to calculate the Present Value (PV) of future cash flows. Changes to this curve are what drive Interest Rate Risk.

1.  **Navigate to the "Discount Curve" page:**
    *   In the sidebar navigation, select "Discount Curve".

2.  **Explore the Baseline Market Rates:**
    *   The page displays a table of "Baseline Market Rates". These are the starting interest rates for various maturities (tenors) such as 1 Month, 1 Year, 10 Years, etc. These rates reflect the current market's expectation of future interest rates.

3.  **Adjust the Liquidity Spread:**
    *   On the sidebar, you'll find a slider for "Liquidity Spread (bps)".
    *   **Concept:** A liquidity spread is an additional premium added to benchmark interest rates to compensate for the difficulty of selling an asset quickly without a significant loss of value. In the context of a bank, it can be added to market rates to reflect the funding costs or specific asset/liability characteristics.
    *   Adjusting this slider will increase or decrease all market rates uniformly by the specified basis points (bps, where 100 bps = 1%).
    *   Observe how the "Rate (Annual)" column in the "Baseline Market Rates" table changes as you adjust the spread.

4.  **Observe the Interpolated Discount Curve:**
    *   The "Baseline Discount Curve" plot visualizes the yield curve. This curve is derived by interpolating the discrete market rates to provide a continuous set of rates for every month up to the longest tenor.
    *   The plot shows "Months to Maturity" on the X-axis and "Rate" on the Y-axis.
    *   As you adjust the "Liquidity Spread", you'll see the entire curve shift up or down in a parallel fashion.

<aside class="positive">
This discount curve is critical because every future cash flow from your generated portfolio (Step 2) will be discounted using a rate from this curve, based on its maturity. Understanding its shape and how it shifts is key to understanding the economic value of your portfolio.
</aside>

## Setting Up IRRBB Simulation Parameters
Duration: 0:10

Now that you have a portfolio and a baseline discount curve, you can set up the parameters for the Interest Rate Risk in the Banking Book (IRRBB) simulation. This page allows you to define behavioral assumptions for certain instruments and select the interest rate shock scenarios.

1.  **Navigate to the "IRRBB Simulation" page:**
    *   In the sidebar navigation, select "IRRBB Simulation".

2.  **Configure Behavioral Assumptions:**
    *   **Concept:** Behavioral assumptions are crucial for realistic IRRBB modeling, as some instruments (like mortgages or non-maturity deposits) do not behave strictly according to their contractual terms.
    *   **Mortgage Prepayment Rate (Annual %):** Use the slider to set an assumed annual prepayment rate for mortgages in the portfolio.
        *   **Concept:** Mortgages often prepay (borrowers pay off their loans early) due to factors like refinancing opportunities when rates fall, or home sales. This changes the actual cash flow profile of these assets.
    *   **Non-Maturity Deposit (NMD) Beta:** Adjust the slider for NMD Beta.
        *   **Concept:** Non-Maturity Deposits (NMDs) like checking and savings accounts technically have no fixed maturity, but banks rely on their stability. NMD Beta models how sensitive the interest rate paid on these deposits is to changes in market rates. A beta of 0.5 means the NMD rate moves by 50% of the market rate change.
    *   **NMD Behavioral Maturity (Years):** Set an assumed behavioral maturity for NMDs.
        *   **Concept:** While NMDs are contractually "on demand," behavioral models assign an average "stickiness" or effective maturity (e.g., 5 years) to them, recognizing that not all funds will be withdrawn simultaneously.

3.  **Select Basel Interest Rate Shock Scenarios:**
    *   **Concept:** Regulators (like those guided by Basel Committee on Banking Supervision) require banks to assess IRRBB under a set of standardized interest rate shock scenarios. These shocks test different vulnerabilities of the banking book.
    *   You can select multiple scenarios from the dropdown menu:
        *   **Parallel Up:** All interest rates across the entire yield curve increase by the same amount.
        *   **Parallel Down:** All interest rates across the entire yield curve decrease by the same amount.
        *   **Steepener:** Short-term rates decrease, while long-term rates increase, making the yield curve steeper.
        *   **Flattener:** Short-term rates increase, while long-term rates decrease, making the yield curve flatter.
        *   **Short Rate Up:** Only short-term rates increase.
        *   **Short Rate Down:** Only short-term rates decrease.

4.  **Define Shock Magnitudes:**
    *   For each scenario, you can specify the "Shock Magnitude (Short-term, bps)" and "Shock Magnitude (Long-term, bps)". These are applied as a change in basis points (100 bps = 1%) to the corresponding parts of the yield curve.

5.  **Adjust Behavioral Shock Adjustment Factor:**
    *   This slider allows you to model how behavioral assumptions (like prepayment) might change specifically under the stress of an interest rate shock.
    *   **Concept:** For example, if interest rates fall (a "Down" scenario), mortgage borrowers are more likely to prepay (refinance). This factor allows you to amplify or dampen the behavioral response to a shock relative to the baseline.

<aside class="negative">
Remember that the behavioral models and shock adjustments in this application are simplified for illustrative purposes. Real-world financial models are far more complex, incorporating detailed statistical analysis and economic forecasts.
</aside>

## Running the IRRBB Simulation
Duration: 0:05

Once all your portfolio, discount curve, and simulation parameters are set, you're ready to run the IRRBB simulation. This will calculate the Economic Value of Equity (EVE) under the baseline scenario and then under each selected interest rate shock scenario.

1.  **Initiate the Simulation:**
    *   After configuring all parameters on the "IRRBB Simulation" page, click the "Run IRRBB Simulation" button in the sidebar.
    *   The application will start processing. A spinner will indicate that the calculations are underway. This may take a few moments depending on the number of instruments and scenarios selected.

2.  **What Happens During the Simulation:**
    *   **Cash Flow Generation:** For every instrument in your portfolio, the application first generates its contractual cash flows (interest and principal payments).
    *   **Behavioral Adjustments (Baseline):** These initial cash flows are then adjusted based on the baseline behavioral assumptions you set (e.g., for mortgages with prepayment options or Non-Maturity Deposits).
    *   **Baseline Valuation:** The present value (PV) of all cash flows (assets and liabilities) is calculated using the baseline discount curve. The **Baseline EVE** is then determined as PV(Assets) - PV(Liabilities).
    *   **Shock Curve Generation:** For each selected interest rate shock scenario, a new "shocked" discount curve is created by applying the specified shock magnitudes (e.g., parallel shift, steepening, flattening) to the baseline curve.
    *   **Floating Rate Repricing:** For floating-rate instruments and hybrid instruments like swaps, their interest cash flows are re-calculated using the new shocked rates from the relevant shocked curve. This reflects how their payments would change in the new rate environment.
    *   **Behavioral Adjustments (Shocked):** The behavioral assumptions (e.g., prepayment rates) are further adjusted based on the "Behavioral Shock Adjustment Factor" to reflect how customer behavior might change under the stress scenario.
    *   **Shocked Valuation:** The present value of all cash flows (now repriced and behaviorally adjusted under the shock) is calculated using the *shocked* discount curve. This gives you the **Shocked EVE**.
    *   **ΔEVE Calculation:** Finally, the **Change in EVE (ΔEVE)** is calculated for each scenario by subtracting the Baseline EVE from the Shocked EVE.

<aside class="positive">
The simulation provides a powerful way to understand the sensitivity of your bank's economic value to different interest rate movements. It goes beyond simple gap analysis by considering the full cash flow profiles and their present values under various conditions.
</aside>

## Analyzing the Economic Value of Equity (EVE) Impact
Duration: 0:10

After the simulation completes, the "EVE Impact Analysis" section on the "IRRBB Simulation" page provides detailed insights into how interest rate shocks affect your bank's economic value.

1.  **View Baseline EVE:**
    *   The "Baseline EVE" is displayed, representing the economic value of your bank's equity under the current market conditions (the unshocked baseline discount curve). This is the starting point for all comparisons.

2.  **Examine ΔEVE Results:**
    *   A table titled "ΔEVE by Scenario" shows the calculated change in EVE for each selected shock scenario.
    *   **ΔEVE (Absolute):** This column shows the raw monetary change in EVE. A negative value indicates a decrease in economic value under that shock scenario.
    *   **ΔEVE (% of Tier 1 Capital):** This is a critical regulatory reporting metric. It expresses the ΔEVE as a percentage of the Tier 1 Capital you defined in the "Portfolio Generation" step. Regulators often set limits on how much ΔEVE a bank can withstand relative to its capital.
        *   For example, a ΔEVE of -15% of Tier 1 Capital means that under that specific interest rate shock, the bank's economic value has eroded by 15% of its core capital, which could be a significant concern.

3.  **Interpret the ΔEVE Bar Chart:**
    *   A bar chart titled "ΔEVE by Basel Interest Rate Shock Scenario (% of Tier 1 Capital)" visually summarizes the impact of each shock.
    *   Each bar represents a different scenario, and its height indicates the ΔEVE as a percentage of Tier 1 Capital.
    *   **Color Coding:** Bars are typically colored green for positive ΔEVE (increase in value) and red for negative ΔEVE (decrease in value).
    *   **Insights:**
        *   **Parallel Up/Down:** These show sensitivity to broad market rate movements. If ΔEVE is negative in a "Parallel Up" scenario, it means the bank's liabilities are more sensitive to rate increases (e.g., floating-rate liabilities repricing faster than floating-rate assets), or fixed-rate assets are hurt more than fixed-rate liabilities.
        *   **Steepener/Flattener:** These test exposure to changes in the *shape* of the yield curve. A negative ΔEVE in a "Steepener" scenario suggests a mismatch where the short end falling and long end rising disproportionately harms the bank's value (e.g., long-term fixed-rate assets funded by short-term floating-rate liabilities).
        *   **Short Rate Up/Down:** These highlight sensitivity to immediate changes in the short end of the curve, often impacting short-term funding and floating-rate instruments.

<aside class="positive">
Analyzing ΔEVE in conjunction with Tier 1 Capital is paramount for regulatory compliance and internal risk management. It highlights which types of interest rate movements pose the greatest threat to the bank's long-term economic stability.
</aside>

## Understanding Net Gap Analysis
Duration: 0:07

In addition to EVE, the application also provides a "Net Gap Analysis," which offers a complementary, simpler view of interest rate risk, typically focusing on cash flows within specific time buckets.

1.  **Purpose of Net Gap Analysis:**
    *   **Concept:** Net Gap analysis is a traditional method for identifying interest rate risk exposures arising from maturity or repricing mismatches within specific time horizons. It provides a snapshot of how much interest-rate-sensitive assets or liabilities mature or reprice within defined "buckets."
    *   Unlike EVE, which considers the present value of all future cash flows over the entire life of instruments, Net Gap focuses on the nominal amount of assets and liabilities due or repricing in defined periods.

2.  **Examine the Net Gap Table:**
    *   The table "Net Gap by Basel Bucket" presents the cash flow mismatches across standardized "Basel Regulatory Buckets." These buckets segment the future into various time periods (e.g., 0-1 Month, 1M-3M, 1Y-2Y, up to 20Y+).
    *   **Total Inflows:** The sum of all positive cash flows (from assets) expected within that bucket.
    *   **Total Outflows:** The sum of all negative cash flows (from liabilities) expected within that bucket. (Note: The application converts these to positive numbers for display as 'outflows').
    *   **Net Gap:** Calculated as Total Inflows - Total Outflows.
        *   A **positive Net Gap** in a bucket means the bank has more assets repricing or maturing than liabilities in that period. This makes the bank "asset sensitive" in that bucket, generally benefiting from rising interest rates within that bucket.
        *   A **negative Net Gap** means the bank has more liabilities repricing or maturing than assets. This makes the bank "liability sensitive" in that bucket, generally benefiting from falling interest rates within that bucket.

3.  **Interpret the Net Gap Bar Chart:**
    *   The bar chart visually represents the "Net Gap Across Basel Buckets."
    *   Each bar corresponds to a time bucket, showing its Net Gap value.
    *   This visual helps quickly identify periods of significant asset or liability sensitivity. For example, a large positive bar in the "6M-1Y" bucket means the bank has a large amount of assets repricing or maturing in that window, making it particularly exposed to rate changes in that specific short-term period.

<aside class="positive">
Net Gap analysis provides a quick and intuitive understanding of a bank's immediate interest rate exposure. While less comprehensive than EVE, it is a valuable tool for managing short-term interest rate risk and identifying liquidity mismatches.
</aside>

## Conclusion and Further Exploration
Duration: 0:03

Congratulations! You have successfully navigated the QuLab application to understand key concepts related to Interest Rate Risk in the Banking Book (IRRBB) and its impact on Economic Value of Equity (EVE).

Through this codelab, you've learned how to:
*   Generate a synthetic banking book portfolio.
*   Understand and manipulate the discount curve, a fundamental valuation tool.
*   Configure behavioral assumptions for instruments like mortgages and non-maturity deposits.
*   Simulate various Basel-mandated interest rate shock scenarios.
*   Analyze the impact of these shocks on a bank's EVE, both in absolute terms and as a percentage of Tier 1 Capital.
*   Perform Net Gap analysis to understand cash flow mismatches across different time buckets.

<aside class="positive">
This application provides a foundational understanding of complex financial risk management concepts. By experimenting with different parameters, you can gain deeper insights into how various portfolio compositions and market conditions affect a bank's interest rate risk profile.
</aside>

**Further Exploration:**
*   Try changing the "Number of Instruments" and observe if the absolute ΔEVE scales proportionally.
*   Experiment with different "Liquidity Spread" values on the "Discount Curve" page and see how it impacts the baseline EVE.
*   Vary the "Behavioral Assumptions" (e.g., increase NMD Behavioral Maturity or Mortgage Prepayment Rate) and re-run simulations to see how these behavioral factors influence ΔEVE under different shock scenarios.
*   Observe how the "Net Gap" chart changes when you create portfolios with a bias towards short-term assets or long-term liabilities.

By continuously exploring and modifying the inputs, you can develop a robust intuition for the dynamics of interest rate risk and its crucial role in banking.
