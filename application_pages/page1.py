
import streamlit as st

def run_page1():
    st.header("Introduction to Lab 5.1: IRRBB Models - Development")
    st.markdown("""
    Welcome to Lab 5.1, focusing on Interest Rate Risk in the Banking Book (IRRBB) with a deep dive into the
    Economic Value of Equity (EVE) framework. This application is designed to help you understand and simulate
    the impact of interest rate changes on a bank's economic value.

    ### What you can do in this lab:

    - **Generate a Synthetic Banking Portfolio:** On the 'Page 2' (IRRBB Analysis) page, you can define parameters
      to create a diverse portfolio of interest-sensitive assets, liabilities, and derivatives.
    - **Project Cash Flows:** The application will project future cash flows for these instruments,
      incorporating important behavioral assumptions like mortgage prepayments and Non-Maturity Deposit (NMD) betas.
    - **Calculate Baseline EVE and Net Gap:** Understand the initial economic value of the portfolio and
      analyze the net gap across various Basel regulatory time buckets.
    - **Simulate Interest Rate Shocks:** Apply the six prescribed Basel interest rate shock scenarios
      (Parallel Up/Down, Steepener, Flattener, Short-Up/Down) to observe their impact on EVE.
    - **Report $\Delta EVE$:** See the change in EVE, reported as a percentage of Tier 1 capital,
      to assess the bank's exposure to interest rate risk.

    ### How to use this application:

    1.  **Navigate to 'Page 2':** Use the sidebar on the left to select "Page 2".
    2.  **Adjust Parameters:** On "Page 2", you will find various input widgets in the sidebar.
        Adjust the number of instruments, Tier 1 Capital, portfolio dates, liquidity spread, and behavioral assumptions
        to customize your simulation.
    3.  **Run Simulation:** Click the "Run IRRBB Simulation" button in the sidebar to initiate the calculations.
        The application will display intermediate steps and final results in the main content area.
    4.  **Analyze Results:** Review the tables and charts showing the portfolio overview, discount curves,
        net gap analysis, baseline EVE, and the critical $\Delta EVE$ report under different scenarios.

    We encourage you to experiment with different parameters to observe their effects on the bank's IRRBB profile.
    """)
