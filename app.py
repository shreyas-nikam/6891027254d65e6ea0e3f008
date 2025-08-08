
import streamlit as st
st.set_page_config(page_title="QuLab", layout="wide")
st.sidebar.image("https://www.quantuniversity.com/assets/img/logo5.jpg")
st.sidebar.divider()
st.title("QuLab")
st.divider()
st.markdown("""
In this lab, we explore the intricacies of Interest Rate Risk in the Banking Book (IRRBB), focusing specifically on the Economic Value of Equity (EVE) framework. The objective is to provide an interactive simulation environment where users can generate synthetic banking portfolios, project cash flows under various behavioral assumptions, and assess the impact of interest rate shocks on a bank's economic value.

### What is IRRBB?

IRRBB refers to the current or prospective risk to a bank's capital and earnings arising from adverse movements in interest rates that affect the bank's banking book positions. These positions are held with the intention of being held to maturity or for liquidity purposes, as opposed to trading book positions which are held for short-term profit from price movements.

### Economic Value of Equity (EVE)

EVE is a key metric in IRRBB, representing the present value of the bank's expected future cash flows from its assets, liabilities, and off-balance sheet items. It provides a static, long-term view of risk, capturing the impact of interest rate changes on the underlying value of the bank.

Mathematically, the baseline EVE is defined as:

$$ EVE_{\text{baseline}} = \sum_{i=1}^{N_A} PV(CF_{A,i}) - \sum_{j=1}^{N_L} PV(CF_{L,j}) $$

Where:
- $N_A$ is the number of assets.
- $N_L$ is the number of liabilities.
- $PV(CF_{A,i})$ is the Present Value of cash flows from asset $i$.
- $PV(CF_{L,j})$ is the Present Value of cash flows from liability $j$.

### Present Value (PV) Calculation

The Present Value of a cash flow ($CF_t$) occurring at time $t$ is calculated by discounting it back to the valuation date using an appropriate discount rate ($r_t$):

$$ PV(CF_t) = \frac{CF_t}{(1 + r_t)^{t}} $$

For a series of cash flows, the total Present Value is the sum of the present values of all individual cash flows:

$$ PV = \sum_{k=1}^{M} \frac{CF_k}{(1 + r_{t_k})^{t_k}} $$

**Important Note on Discounting:** The discount rate used here is typically a risk-free rate (e.g., government bond yield curve) plus a liquidity spread. It explicitly excludes commercial margins, as these are considered part of the business's profitability and not directly related to interest rate risk on the balance sheet.

### Change in Economic Value of Equity ($\Delta EVE$)

$\Delta EVE$ measures the sensitivity of a bank's economic value to changes in interest rates. It is the difference between the EVE under a shocked interest rate scenario and the baseline EVE:

$$ \Delta EVE = EVE_{\text{shocked}} - EVE_{\text{baseline}} $$

To standardize reporting and facilitate comparison across institutions, $\Delta EVE$ is often expressed as a percentage of Tier 1 Capital:

$$ \Delta EVE (\% \text{ Tier 1 Capital}) = \frac{\Delta EVE}{\text{Tier 1 Capital}} \times 100\% $$

### Cash Flow Generation and Behavioral Assumptions

Accurate cash flow projection is crucial for EVE calculation. This involves:
- **Fixed vs. Floating Rates:** Distinguishing between instruments with fixed interest payments and those with floating rates that reprice based on market benchmarks.
- **Mortgage Prepayment:** Incorporating behavioral models for mortgage prepayments, where borrowers may repay their loans early, impacting future cash inflows.
- **Non-Maturity Deposit (NMD) Beta ($\beta$):** Modeling the sensitivity of NMD rates (e.g., checking accounts) to changes in market interest rates. NMDs typically do not have a contractual maturity, so behavioral assumptions are essential to assign an effective duration.

### Basel Six Interest Rate Shock Scenarios

Regulatory frameworks, such as Basel III, prescribe specific interest rate shock scenarios to assess IRRBB. These include:
1.  Parallel Up
2.  Parallel Down
3.  Steepener (short rates down, long rates up)
4.  Flattener (short rates up, long rates down)
5.  Short-Term Rate Up
6.  Short-Term Rate Down

### Net Gap Analysis

Net Gap analysis provides a complementary view to EVE by summarizing the difference between interest-sensitive assets and liabilities maturing or repricing within defined time buckets. It offers a short-to-medium term liquidity and earnings perspective.

$$ Net\ Gap_{\text{bucket } k} = \sum_{\text{assets in bucket } k} CF_{\text{in}} - \sum_{\text{liabilities in bucket } k} CF_{\text{out}} $$

This application will enable you to interactively explore these concepts and visualize the impact of various parameters on a bank's IRRBB profile.
""")
# Your code starts here
page = st.sidebar.selectbox(label="Navigation", options=["Portfolio Generation", "IRRBB Analysis", "About"]) # Renamed for clarity
if page == "Portfolio Generation":
    from application_pages.page1 import run_page1
    run_page1()
elif page == "IRRBB Analysis":
    from application_pages.page2 import run_page2
    run_page2()
elif page == "About":
    from application_pages.page3 import run_page3
    run_page3()
# Your code ends


# License
st.caption('''
---
## QuantUniversity License

© QuantUniversity 2025  
This notebook was created for **educational purposes only** and is **not intended for commercial use**.  

- You **may not copy, share, or redistribute** this notebook **without explicit permission** from QuantUniversity.  
- You **may not delete or modify this license cell** without authorization.  
- This notebook was generated using **QuCreate**, an AI-powered assistant.  
- Content generated by AI may contain **hallucinated or incorrect information**. Please **verify before using**.  

All rights reserved. For permissions or commercial licensing, contact: [info@quantuniversity.com](mailto:info@quantuniversity.com)
''')
