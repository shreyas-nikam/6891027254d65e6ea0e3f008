"""
import streamlit as st

st.set_page_config(page_title="QuLab", layout="wide")
st.sidebar.image("https://www.quantuniversity.com/assets/img/logo5.jpg")
st.sidebar.divider()
st.title("QuLab")
st.divider()

st.markdown("""
In this lab, we will explore Interest Rate Risk in the Banking Book (IRRBB) with a focus on the Economic Value of Equity (EVE). This application allows you to simulate the impact of interest rate shocks on a bank's economic value.

**Key Concepts:**

*   **IRRBB:** Interest Rate Risk in the Banking Book - the risk to a bank's earnings and capital arising from changes in interest rates.
*   **EVE (Economic Value of Equity):**  The difference between the present value of a bank's assets and the present value of its liabilities.  It represents the bank's net worth from an economic perspective.
*   **ΔEVE:** The change in EVE resulting from a defined interest rate shock. Regulators use this as a key metric to assess IRRBB.
*   **Net Gap:** The difference between interest rate sensitive assets and liabilities in a given time bucket. It provides a simplified view of a bank's exposure to interest rate risk.

**Mathematical Definitions:**

*   **Economic Value of Equity (EVE):**
    
    $ EVE_{\text{baseline}} = \sum_{i=1}^{N_A} PV(CF_{A,i}) - \sum_{j=1}^{N_L} PV(CF_{L,j}) $
    
    Where:
    *   $N_A$ is the number of assets.
    *   $N_L$ is the number of liabilities.
    *   $PV(CF_{A,i})$ is the present value of the cash flows of asset $i$.
    *   $PV(CF_{L,j})$ is the present value of the cash flows of liability $j$.

*   **Present Value (PV) Calculation:**
    
    $ PV(CF_t) = \frac{CF_t}{(1 + r_t)^{t}} $
    
    or
    
    $ PV = \sum_{k=1}^{M} \frac{CF_k}{(1 + r_{t_k})^{t_k}} $
    
    Where:
    *   $CF_t$ is the cash flow at time t.
    *   $r_t$ is the discount rate for time t.
    *   $r_{t_k}$ is the discount rate for time $t_k$.

*   **Change in Economic Value of Equity (ΔEVE):**
    
    $ \Delta EVE = EVE_{\text{shocked}} - EVE_{\text{baseline}} $
    
    $ \Delta EVE (\% \text{ Tier 1 Capital}) = \frac{\Delta EVE}{\text{Tier 1 Capital}} \times 100\% $

*   **Net Gap Analysis:**
    
    $ Net\ Gap_{\text{bucket } k} = \sum_{\text{assets in bucket } k} CF_{\text{in}} - \sum_{\text{liabilities in bucket } k} CF_{\text{out}} $

""")

# Your code starts here
page = st.sidebar.selectbox(
    label="Navigation",
    options=["Portfolio Generation", "Discount Curve", "IRRBB Simulation"]
)

if page == "Portfolio Generation":
    from application_pages.portfolio_generation import run_portfolio_generation
    run_portfolio_generation()
elif page == "Discount Curve":
    from application_pages.discount_curve import run_discount_curve
    run_discount_curve()
elif page == "IRRBB Simulation":
    from application_pages.irrbb_simulation import run_irrbb_simulation
    run_irrbb_simulation()
# Your code ends
"""