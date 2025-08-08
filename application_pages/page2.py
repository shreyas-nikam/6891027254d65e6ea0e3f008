
import streamlit as st
import pandas as pd
from datetime import datetime
from irrbb_core_functions import (
    create_baseline_discount_curve,
    generate_all_cash_flows,
    map_cashflows_to_basel_buckets,
    calculate_net_gap,
    save_data_to_parquet,
    calculate_present_value_for_cashflows,
    calculate_eve
)
from app import valuation_date, standard_tenors_months, market_rates_data, basel_bucket_definitions_list, convert_tenor_curve_to_date_curve

def run_page2():
    st.header("2. Cash Flow & Gap Analysis")
    st.markdown("""
    This section focuses on projecting the cash flows from your generated portfolio and analyzing the interest rate risk through a Net Gap analysis. 
    The application will first construct a baseline discount curve, then generate detailed cash flows for each instrument, 
    applying behavioral assumptions like mortgage prepayment and Non-Maturity Deposit (NMD) behavior. 
    Finally, these cash flows are mapped into regulatory time buckets to compute the net gap.

    **Mathematical Concepts:**
    *   **Discount Curve**: Used to bring future cash flows back to their present value. It's constructed from market rates and adjusted for liquidity spreads.
    *   **Cash Flow Projection**: Each instrument's cash flows (interest and principal) are projected based on its terms (fixed/floating rate, payment frequency, maturity).
    *   **Behavioral Adjustments**: For certain products:
        *   **Mortgage Prepayment**: Loans may be repaid earlier than their contractual maturity. The model uses a constant annual prepayment rate to adjust future principal cash flows.
        *   **Non-Maturity Deposits (NMDs)**: These are deposits without a fixed maturity. A portion is considered "core" and is assumed to have a behavioral maturity, while the remaining is treated as callable on demand. The **NMD Beta** represents the stable portion of these deposits.
    *   **Net Gap**: The difference between interest-sensitive assets and liabilities maturing or repricing within a specific time bucket. A positive gap indicates asset sensitivity, while a negative gap indicates liability sensitivity.

    **Key Model Parameters:**
    *   **Liquidity Spread (bps)**: An additional spread applied to the risk-free rate to reflect liquidity premiums in the discount curve.
    *   **Mortgage Prepayment Rate (Annual)**: The annual rate at which mortgages are assumed to prepay. (e.g., 0.05 for 5% annually)
    *   **NMD Beta**: The proportion of Non-Maturity Deposits considered "stable" and assigned a behavioral maturity (e.g., 0.5 for 50% stable).
    *   **NMD Behavioral Maturity (Years)**: The assumed average maturity for the stable portion of NMDs.
    
    """)

    if 'taiwan_portfolio_df' not in st.session_state or st.session_state['taiwan_portfolio_df'].empty:
        st.warning("Please go to 'Portfolio Generation' page and generate a portfolio first.")
        return

    st.markdown("---")
    st.subheader("Model Parameters")
    with st.sidebar.expander("Model Parameters", expanded=True):
        liquidity_spread_bps = st.number_input(
            "Liquidity Spread (bps)",
            min_value=0,
            max_value=100,
            value=10,
            step=1,
            help="Basis points added to the risk-free rate to form the discount curve."
        )
        mortgage_prepayment_rate_annual = st.number_input(
            "Mortgage Prepayment Rate (Annual)",
            min_value=0.0,
            max_value=0.5,
            value=0.05,
            step=0.01,
            format="%f",
            help="Annual rate at which mortgages are assumed to prepay (e.g., 0.05 for 5%)."
        )
        nmd_beta = st.number_input(
            "NMD Beta",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            step=0.05,
            format="%f",
            help="Proportion of Non-Maturity Deposits considered stable (e.g., 0.5 for 50%)."
        )
        nmd_behavioral_maturity_years = st.number_input(
            "NMD Behavioral Maturity (Years)",
            min_value=1.0,
            max_value=10.0,
            value=3.0,
            step=0.5,
            format="%f",
            help="Assumed average maturity for the stable portion of NMDs."
        )
        behavioral_shock_adjustment_factor = st.number_input(
            "Behavioral Shock Adjustment Factor",
            min_value=0.0,
            max_value=0.5,
            value=0.10,
            step=0.01,
            format="%f",
            help="Factor by which behavioral assumptions (e.g., prepayment) are adjusted under shock scenarios."
        )

    st.session_state['liquidity_spread_bps'] = liquidity_spread_bps
    st.session_state['mortgage_prepayment_rate_annual'] = mortgage_prepayment_rate_annual
    st.session_state['nmd_beta'] = nmd_beta
    st.session_state['nmd_behavioral_maturity_years'] = nmd_behavioral_maturity_years
    st.session_state['behavioral_shock_adjustment_factor'] = behavioral_shock_adjustment_factor

    if st.button("Run Cash Flow & Gap Analysis", help="Click to generate cash flows, discount curve, and calculate net gap."):
        with st.spinner("Running cash flow and gap analysis..."):
            # 1. Create Baseline Discount Curve
            baseline_discount_curve_df = create_baseline_discount_curve(
                valuation_date,
                market_rates_data,
                standard_tenors_months,
                liquidity_spread_bps
            )
            st.session_state['baseline_discount_curve_df'] = baseline_discount_curve_df
            st.session_state['baseline_date_curve_df'] = convert_tenor_curve_to_date_curve(baseline_discount_curve_df, valuation_date)
            st.success("Baseline Discount Curve Created!")

            # 2. Generate All Cash Flows
            all_cash_flows = generate_all_cash_flows(
                st.session_state['taiwan_portfolio_df'],
                st.session_state['baseline_date_curve_df'],
                valuation_date,
                mortgage_prepayment_rate_annual,
                nmd_beta,
                nmd_behavioral_maturity_years
            )
            st.session_state['all_cash_flows'] = all_cash_flows
            st.success(f"Generated {len(all_cash_flows)} cash flows.")

            # 3. Map Cash Flows to Basel Buckets
            bucketted_cash_flows_df = map_cashflows_to_basel_buckets(
                all_cash_flows, valuation_date, basel_bucket_definitions_list
            )
            st.session_state['bucketted_cash_flows_df'] = bucketted_cash_flows_df
            st.success("Cash flows mapped to Basel buckets.")

            # 4. Calculate Baseline EVE
            if not bucketted_cash_flows_df.empty:
                pv_assets_baseline, pv_liabilities_baseline = calculate_present_value_for_cashflows(
                    bucketted_cash_flows_df,
                    st.session_state['baseline_date_curve_df'],
                    valuation_date
                )
                baseline_eve = calculate_eve(pv_assets_baseline, pv_liabilities_baseline)
                st.session_state['baseline_eve'] = baseline_eve
                st.session_state['pv_assets_baseline'] = pv_assets_baseline
                st.session_state['pv_liabilities_baseline'] = pv_liabilities_baseline
                st.success(f"Baseline EVE calculated: {baseline_eve:,.2f} TWD")
            else:
                st.warning("No cash flows generated to calculate Baseline EVE.")
                st.session_state['baseline_eve'] = 0.0
                st.session_state['pv_assets_baseline'] = 0.0
                st.session_state['pv_liabilities_baseline'] = 0.0

            # 5. Calculate Net Gap
            net_gap_table_df = calculate_net_gap(bucketted_cash_flows_df)
            st.session_state['net_gap_table_df'] = net_gap_table_df
            save_data_to_parquet(net_gap_table_df, "gap_table.parquet")
            st.success("Net Gap table calculated and saved to gap_table.parquet.")

    st.markdown("---")
    st.subheader("Results")

    if 'baseline_discount_curve_df' in st.session_state and not st.session_state['baseline_discount_curve_df'].empty:
        st.write("### Baseline Discount Curve")
        st.dataframe(st.session_state['baseline_discount_curve_df'])
    
    if 'bucketted_cash_flows_df' in st.session_state and not st.session_state['bucketted_cash_flows_df'].empty:
        st.write("### First 5 Rows of Cash Flows with Basel Buckets")
        st.dataframe(st.session_state['bucketted_cash_flows_df'].head())
        st.markdown(f"**Total Cash Flows Generated (Future CFs):** {len(st.session_state['all_cash_flows'])}")
    
    if 'net_gap_table_df' in st.session_state and not st.session_state['net_gap_table_df'].empty:
        st.write("### Net Gap Table")
        st.dataframe(st.session_state['net_gap_table_df'])
        st.download_button(
            label="Download Gap Table as Parquet",
            data=open("gap_table.parquet", "rb").read(),
            file_name="gap_table.parquet",
            mime="application/octet-stream",
            help="Download the calculated net gap table."
        )

    if 'baseline_eve' in st.session_state:
        st.markdown(f"**Baseline EVE:** {st.session_state['baseline_eve']:,.2f} TWD")
        st.markdown(f"**PV of Assets (Baseline):** {st.session_state['pv_assets_baseline']:,.2f} TWD")
        st.markdown(f"**PV of Liabilities (Baseline):** {st.session_state['pv_liabilities_baseline']:,.2f} TWD")



