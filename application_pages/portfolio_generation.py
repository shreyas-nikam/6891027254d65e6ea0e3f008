import streamlit as st
import pandas as pd
from datetime import date
from utils import generate_synthetic_portfolio, market_rates_data, standard_tenors_months, basel_bucket_definitions_list, shock_scenarios, create_baseline_discount_curve, convert_tenor_curve_to_date_curve, calculate_cashflows_for_instrument, apply_behavioral_assumptions, map_cashflows_to_basel_buckets, calculate_present_value_for_cashflows, calculate_eve, calculate_net_gap, generate_basel_shocked_curve, reprice_floating_instrument_cashflows_under_shock, adjust_behavioral_assumptions_for_shock, recalculate_cashflows_and_pv_for_scenario, calculate_delta_eve, report_delta_eve_as_percentage_of_tier1, plot_delta_eve_bar_chart

def run_portfolio_generation():
    st.header("Portfolio Generation")
    st.markdown("""
    This page allows you to generate a synthetic banking book portfolio. You can configure the number of instruments, 
    Tier 1 capital, and the time frame for the portfolio generation.

    The generated portfolio will include a mix of assets (Loans, Bonds, Mortgages) and liabilities (Deposits), 
    along with Swaps. Each instrument will have characteristics such as issue date, maturity date, amount, rate type 
    (Fixed, Floating, Hybrid), coupon rate, payment frequency, and specific features like prepayment options for 
    mortgages or Non-Maturity Deposit (NMD) flags.
    """)

    st.subheader("Portfolio Generation Parameters")

    # Input Widgets
    num_instruments = st.sidebar.slider(
        label="Number of Instruments",
        min_value=1,
        max_value=100,
        value=25,
        step=1,
        help="Number of synthetic financial instruments to generate in the portfolio."
    )

    tier1_capital_val = st.sidebar.number_input(
        label="Tier 1 Capital (TWD)",
        min_value=10_000_000,
        value=1_000_000_000,
        step=10_000_000,
        format="%d",
        help="The amount of Tier 1 Capital the bank holds. Used for risk reporting."
    )

    start_date_gen = st.sidebar.date_input(
        label="Portfolio Start Date",
        value=date(2023, 1, 1),
        help="The earliest possible issue date for instruments in the portfolio."
    )

    end_date_gen = st.sidebar.date_input(
        label="Portfolio End Date",
        value=date(2050, 12, 31),
        help="The latest possible maturity date for instruments in the portfolio."
    )

    valuation_date = st.sidebar.date_input(
        label="Valuation Date",
        value=date.today(),
        help="The date as of which the portfolio and its cashflows are valued."
    )

    if st.sidebar.button("Generate Portfolio"):
        with st.spinner("Generating synthetic portfolio..."):
            taiwan_portfolio_df = generate_synthetic_portfolio(num_instruments, tier1_capital_val, start_date_gen, end_date_gen)
            st.session_state["taiwan_portfolio_df"] = taiwan_portfolio_df
            st.session_state["valuation_date"] = valuation_date
            st.session_state["tier1_capital_val"] = tier1_capital_val
        st.success("Portfolio generated successfully!")

    if "taiwan_portfolio_df" in st.session_state:
        st.subheader("Initial Portfolio Overview")
        st.write("The first few rows of the generated portfolio:")
        st.dataframe(st.session_state["taiwan_portfolio_df"].head())
        
        st.expander("View Full Portfolio Data").dataframe(st.session_state["taiwan_portfolio_df"])

        # Display some summary statistics
        st.subheader("Portfolio Summary Statistics")
        col1, col2, col3 = st.columns(3)
        total_assets = st.session_state["taiwan_portfolio_df"][st.session_state["taiwan_portfolio_df"]["Is_Asset"]]["Amount"].sum()
        total_liabilities = st.session_state["taiwan_portfolio_df"][~st.session_state["taiwan_portfolio_df"]["Is_Asset"]]["Amount"].sum()

        col1.metric("Total Instruments", len(st.session_state["taiwan_portfolio_df"]))
        col2.metric("Total Asset Notional", f"{total_assets:,.0f} TWD")
        col3.metric("Total Liability Notional", f"{total_liabilities:,.0f} TWD")

        st.write("\n")


