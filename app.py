"""import streamlit as st
st.set_page_config(page_title=\"QuLab\", layout=\"wide\")
st.sidebar.image(\"https://www.quantuniversity.com/assets/img/logo5.jpg\")
st.sidebar.divider()
st.title(\"QuLab\")
st.divider()
st.markdown("""
In this lab, we will explore Interest Rate Risk in the Banking Book (IRRBB) using a full-revaluation Economic Value of Equity (EVE) engine. This application allows you to:

*   Assemble a banking-book positions dataset that captures interest-sensitive assets, liabilities, and (optionally) simple hedges.
*   Generate synthetic cash-flow data for those positions, respecting product features and behavioural assumptions.
*   Build a full-revaluation IRRBB engine that computes baseline present values, allocates cash flows into regulatory time buckets, and estimates $\Delta EVE$ under the Basel six-scenario shock set.
*   Report $\Delta EVE$ as a percentage of Tier 1 capital and interpret the risk signal of each scenario.

### Mathematical Foundation

The Present Value (PV) of a series of cash flows is the sum of the present values of each individual cash flow. For a single cash flow $CF_t$ received at time $t$, discounted at a rate $r_t$:

$$
PV(CF_t) = \frac{CF_t}{(1 + r_t)^{t}}
$$

For a series of cash flows $CF_1, CF_2, \ldots, CF_M$ occurring at times $t_1, t_2, \ldots, t_M$:

$$
PV = \sum_{k=1}^{M} \frac{CF_k}{(1 + r_{t_k})^{t_k}}
$$

For EVE calculation, the cash flows will be discounted using a risk-free yield curve plus an appropriate liquidity spread; commercial margins are excluded.

### Net Gap

The net gap for each time bucket represents the difference between total cash inflows (from assets) and total cash outflows (from liabilities and derivatives) within that bucket:

$$
Net\ Gap_{\text{bucket } k} = \sum_{\text{assets in bucket } k} CF_{\text{in}} - \sum_{\text{liabilities in bucket } k} CF_{\text{out}}
$$

$\Delta EVE$ measures the change in a bank's EVE due to an interest rate shock:

$$
\Delta EVE = EVE_{\text{shocked}} - EVE_{\text{baseline}}
$$

$\Delta EVE$ will be reported as a percentage of Tier 1 capital, allowing for a standardized interpretation of the risk signal:

$$
\Delta EVE (\% \text{ Tier 1 Capital}) = \frac{\Delta EVE}{\text{Tier 1 Capital}} \times 100\%
$$


""")

# Your code starts here
page = st.sidebar.selectbox(label=\"Navigation\", options=[\"Portfolio Generation\", \"Cash Flow Analysis\", \"IRRBB Simulation\"])

if page == \"Portfolio Generation\":
    from application_pages.portfolio_generation import run_portfolio_generation
    run_portfolio_generation()
elif page == \"Cash Flow Analysis\":
    from application_pages.cash_flow_analysis import run_cash_flow_analysis
    run_cash_flow_analysis()
elif page == \"IRRBB Simulation\":
    from application_pages.irrbb_simulation import run_irrbb_simulation
    run_irrbb_simulation()
# Your code ends
""