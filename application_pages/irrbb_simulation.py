"""import streamlit as st
import pandas as pd
from datetime import datetime
import pickle
from application_pages.utils import (
    valuation_date,
    market_rates_data,
    standard_tenors_months,
    basel_bucket_definitions_list,
    shock_scenarios,
    create_baseline_discount_curve,
    generate_basel_shocked_curve,
    recalculate_cashflows_and_pv_for_scenario,
    calculate_delta_eve,
    report_delta_eve_as_percentage_of_tier1,
    plot_delta_eve_bar_chart,
    save_model_artifact,
    save_data_to_parquet
)

def run_irrbb_simulation():
    st.header("IRRBB Simulation Results")
    st.markdown("""
    This page simulates the impact of various Basel interest rate shock scenarios on the Economic Value of Equity (EVE).
    The engine calculates the change in EVE ($\Delta EVE$) under each scenario and reports it as a percentage of Tier 1 Capital.

    $$
    \Delta EVE = EVE_{\text{shocked}} - EVE_{\text{baseline}}
    $$

    $$
    \Delta EVE (\% \text{ Tier 1 Capital}) = \frac{\Delta EVE}{\text{Tier 1 Capital}} \times 100\%
    $$
    """)

    # Check for required data in session state
    required_keys = [
        'taiwan_portfolio_df', 'baseline_discount_curve_df', 'baseline_date_curve_df',
        'baseline_eve', 'liquidity_spread_bps', 'mortgage_prepayment_rate_annual',
        'nmd_beta', 'nmd_behavioral_maturity_years'
    ]
    for key in required_keys:
        if key not in st.session_state or st.session_state[key] is None:
            st.warning(f"Please complete 'Portfolio Generation' and 'Cash Flow Analysis' pages first. Missing: {key}")
            return

    portfolio_df = st.session_state['taiwan_portfolio_df']
    baseline_discount_curve_df = st.session_state['baseline_discount_curve_df']
    baseline_date_curve_df = st.session_state['baseline_date_curve_df']
    baseline_eve = st.session_state['baseline_eve']
    tier1_capital_val = st.session_state.get('tier1_capital', 1_000_000_000) # Get from session state, default if not set

    # Retrieve behavioral parameters from session state
    liquidity_spread_bps_val = st.session_state['liquidity_spread_bps']
    mortgage_prepayment_rate_annual_val = st.session_state['mortgage_prepayment_rate_annual']
    nmd_beta_val = st.session_state['nmd_beta']
    nmd_behavioral_maturity_years_val = st.session_state['nmd_behavioral_maturity_years']

    st.markdown("---")
    st.subheader("Run IRRBB Simulation")
    st.markdown("Click the button below to run the IRRBB simulation across all Basel shock scenarios.")

    if st.button("Run IRRBB Simulation"):
        shocked_eves = {}
        delta_eve_values = {}
        total_scenarios = len(shock_scenarios)
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, (scenario_name, shock_params) in enumerate(shock_scenarios.items()):
            status_text.text(f"Running scenario: {scenario_name} ({i+1}/{total_scenarios})")

            shocked_curve_df = generate_basel_shocked_curve(
                baseline_discount_curve_df,
                scenario_name,
                shock_params['short'],
                shock_params['long']
            )

            shocked_eve = recalculate_cashflows_and_pv_for_scenario(
                portfolio_df,
                shocked_curve_df,
                valuation_date,
                scenario_name,
                baseline_date_curve_df, # Pass baseline_date_curve_df
                mortgage_prepayment_rate_annual_val,
                0.10, # Behavioral Shock Adjustment Factor (fixed as per spec, or make input)
                nmd_beta_val,
                nmd_behavioral_maturity_years_val
            )
            shocked_eves[scenario_name] = shocked_eve
            delta_eve_values[scenario_name] = calculate_delta_eve(baseline_eve, shocked_eve)
            progress_bar.progress((i + 1) / total_scenarios)
        
        st.session_state['shocked_eves'] = shocked_eves
        st.session_state['delta_eve_values'] = delta_eve_values
        st.success("Simulation Complete!")

    if 'delta_eve_values' in st.session_state and st.session_state['delta_eve_values']:
        delta_eve_report_df = report_delta_eve_as_percentage_of_tier1(
            st.session_state['delta_eve_values'],
            tier1_capital_val
        )
        st.session_state['delta_eve_report_df'] = delta_eve_report_df

        st.markdown("---")
        st.subheader("Delta EVE Report (% of Tier 1 Capital)")
        st.dataframe(delta_eve_report_df)

        st.subheader("Delta EVE by Basel Interest Rate Shock Scenario")
        plot_delta_eve_bar_chart(delta_eve_report_df)

        st.markdown("---")
        st.subheader("Summary of Results")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Baseline EVE (TWD)", f"{baseline_eve:,.2f}")
        with col2:
            st.metric("Scenarios Analyzed", len(shock_scenarios))

        # Model Persistence
        model_artifact = {
            'valuation_date': valuation_date,
            'baseline_discount_curve_df': baseline_discount_curve_df,
            'tier1_capital_val': tier1_capital_val,
            'baseline_eve': baseline_eve,
            'shocked_eves': st.session_state['shocked_eves'],
            'delta_eve_report_df': delta_eve_report_df
        }
        save_model_artifact(model_artifact, 'irrbb_gap_eve_model.pkl')

        with open('irrbb_gap_eve_model.pkl', 'rb') as f:
            st.download_button(
                label="Download irrbb_gap_eve_model.pkl",
                data=f,
                file_name="irrbb_gap_eve_model.pkl",
                mime='application/octet-stream',
            )


if __name__ == "__main__":
    run_irrbb_simulation()
"""