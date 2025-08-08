"""import streamlit as st
import pandas as pd
from datetime import datetime
from application_pages.utils import (
    create_baseline_discount_curve,
    generate_all_cash_flows,
    map_cashflows_to_basel_buckets,
    calculate_present_value_for_cashflows,
    calculate_eve,
    calculate_net_gap,
    convert_tenor_curve_to_date_curve,
    valuation_date,
    market_rates_data,
    standard_tenors_months,
    basel_bucket_definitions_list,
    save_data_to_parquet
)

def run_cash_flow_analysis():
    st.header("Cash Flow Analysis")
    st.markdown("""
    This section focuses on generating and analyzing cash flows from the synthetic banking book portfolio.
    You can adjust model parameters to observe their impact on cash flows and the Net Gap.
    The Present Value (PV) of a series of cash flows is calculated using a baseline discount curve. For a single cash flow $CF_t$ received at time $t$, discounted at a rate $r_t$:

    $$
    PV(CF_t) = \frac{CF_t}{(1 + r_t)^{t}}
    $$

    The Net Gap for each time bucket represents the difference between total cash inflows (from assets) and total cash outflows (from liabilities):

    $$
    Net\ Gap_{\text{bucket } k} = \sum_{\text{assets in bucket } k} CF_{\text{in}} - \sum_{\text{liabilities in bucket } k} CF_{\text{out}}
    $$
    """)

    if 'taiwan_portfolio_df' not in st.session_state or st.session_state['taiwan_portfolio_df'] is None:
        st.warning("Please generate a portfolio first on the 'Portfolio Generation' page.")
        return

    portfolio_df = st.session_state['taiwan_portfolio_df']
    tier1_capital_val = st.session_state.get('tier1_capital', 1_000_000_000)

    st.subheader("Model Parameters")
    liquidity_spread_bps_val = st.sidebar.number_input(
        "Liquidity Spread (bps)", min_value=0, value=10, step=1, help="Spread added to the risk-free rate to reflect liquidity costs."
    )
    mortgage_prepayment_rate_annual_val = st.sidebar.number_input(
        "Mortgage Prepayment Rate (Annual)", min_value=0.0, max_value=1.0, value=0.05, step=0.01, format="%.2f",
        help="Annual rate at which mortgages are expected to prepay."
    )
    nmd_beta_val = st.sidebar.number_input(
        "NMD Beta", min_value=0.0, max_value=1.0, value=0.5, step=0.01, format="%.2f",
        help="Proportion of Non-Maturity Deposits (NMD) that is non-volatile and behaves like longer-term funding."
    )
    nmd_behavioral_maturity_years_val = st.sidebar.number_input(
        "NMD Behavioral Maturity (Years)", min_value=0.0, value=3.0, step=0.5, format="%.1f",
        help="The assumed behavioral maturity for the stable portion of NMDs."
    )

    # Store parameters in session state for other pages
    st.session_state['liquidity_spread_bps'] = liquidity_spread_bps_val
    st.session_state['mortgage_prepayment_rate_annual'] = mortgage_prepayment_rate_annual_val
    st.session_state['nmd_beta'] = nmd_beta_val
    st.session_state['nmd_behavioral_maturity_years'] = nmd_behavioral_maturity_years_val

    st.markdown("---")
    st.subheader("Baseline Discount Curve")
    baseline_discount_curve_df = create_baseline_discount_curve(
        valuation_date,
        market_rates_data,
        standard_tenors_months,
        liquidity_spread_bps_val
    )
    st.dataframe(baseline_discount_curve_df)
    st.session_state['baseline_discount_curve_df'] = baseline_discount_curve_df
    st.session_state['baseline_date_curve_df'] = convert_tenor_curve_to_date_curve(baseline_discount_curve_df, valuation_date)

    st.markdown("---")
    st.subheader("Cash Flow Generation and Bucketing")
    with st.spinner("Generating and bucketing cash flows... This may take a moment."):
        all_cash_flows = generate_all_cash_flows(
            portfolio_df,
            st.session_state['baseline_date_curve_df'],
            valuation_date,
            mortgage_prepayment_rate_annual_val,
            nmd_beta_val,
            nmd_behavioral_maturity_years_val
        )
        st.session_state['all_cash_flows'] = all_cash_flows

        bucketted_cash_flows_df = map_cashflows_to_basel_buckets(
            all_cash_flows,
            valuation_date,
            basel_bucket_definitions_list
        )
        st.session_state['bucketted_cash_flows_df'] = bucketted_cash_flows_df

    st.info(f"Total Cash Flows Generated: {len(all_cash_flows):,}")
    st.info(f"Total Instruments Analyzed: {len(portfolio_df):,}")

    st.subheader("First N rows of Cash Flows with Basel Buckets")
    num_rows_to_display = st.slider("Number of cash flow rows to display", min_value=5, max_value=50, value=10)
    if not bucketted_cash_flows_df.empty:
        st.dataframe(bucketted_cash_flows_df.head(num_rows_to_display))
    else:
        st.info("No cash flows generated for display.")

    st.markdown("---")
    st.subheader("Net Gap Table")
    net_gap_table_df = calculate_net_gap(bucketted_cash_flows_df)
    st.session_state['net_gap_table_df'] = net_gap_table_df

    if not net_gap_table_df.empty:
        st.dataframe(net_gap_table_df)
        st.download_button(
            label="Download gap_table.parquet",
            data=save_data_to_parquet(net_gap_table_df, "gap_table.parquet"),
            file_name="gap_table.parquet",
            mime='application/octet-stream',
        )
    else:
        st.info("No net gap data to display.")

    # Calculate Baseline EVE
    pv_assets_baseline, pv_liabilities_baseline = calculate_present_value_for_cashflows(
        all_cash_flows, baseline_discount_curve_df, valuation_date
    )
    baseline_eve = calculate_eve(pv_assets_baseline, pv_liabilities_baseline)
    st.session_state['baseline_eve'] = baseline_eve
    st.session_state['pv_assets_baseline'] = pv_assets_baseline
    st.session_state['pv_liabilities_baseline'] = pv_liabilities_baseline

    st.markdown("---")
    st.subheader("Summary Metrics")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Baseline EVE (TWD)", f"{baseline_eve:,.2f}")
    with col2:
        st.metric("Total Tier 1 Capital (TWD)", f"{tier1_capital_val:,.2f}")


if __name__ == "__main__":
    run_cash_flow_analysis()
"""