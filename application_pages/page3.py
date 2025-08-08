
import streamlit as st
import pandas as pd
from datetime import datetime
import pickle
from irrbb_core_functions import (
    generate_basel_shocked_curve,
    recalculate_cashflows_and_pv_for_scenario,
    calculate_delta_eve,
    report_delta_eve_as_percentage_of_tier1,
    save_model_artifact
)
from app import valuation_date, standard_tenors_months, shock_scenarios, plot_delta_eve_bar_chart, convert_tenor_curve_to_date_curve

def run_page3():
    st.header("3. IRRBB Simulation Results")
    st.markdown("""
    This final section presents the core Interest Rate Risk in the Banking Book (IRRBB) simulation results.
    Here, the application applies various **Basel interest rate shock scenarios** to the portfolio, 
    re-calculates the cash flows and Economic Value of Equity (EVE) under each shocked curve, 
    and then determines the **change in EVE ($\Delta EVE$)** from the baseline.

    **Mathematical Concepts:**
    *   **Interest Rate Shock Scenarios**: The Basel framework prescribes six standardized scenarios to assess IRRBB. These include parallel shifts (up/down), twists (steepener/flattener), and short-rate shocks.
    *   **Revaluation under Shock**: For each scenario, a new shocked discount curve is generated. Floating-rate instruments' cash flows are repriced using this new curve, and behavioral assumptions (like prepayment) are adjusted if applicable.
    *   **$\Delta EVE$ Calculation**: The difference between the EVE calculated under a shocked scenario and the baseline EVE. A positive $\Delta EVE$ means EVE increased under the shock, while a negative $\Delta EVE$ means EVE decreased.
    *   **Reporting as % of Tier 1 Capital**: To standardize risk assessment across banks of different sizes, $\Delta EVE$ is often reported as a percentage of the bank's Tier 1 Capital.

    **Simulation Process:**
    1.  **Check Prerequisites**: Ensure that a portfolio has been generated and cash flow analysis completed on previous pages.
    2.  **Iterate Scenarios**: For each of the six Basel scenarios:
        *   Generate a **shocked discount curve**.
        *   **Recalculate all cash flows and their present values** considering the new shocked curve and adjusted behavioral parameters.
        *   Compute the **shocked EVE**.
    3.  **Calculate $\Delta EVE$**: Determine the change in EVE for each scenario relative to the baseline EVE.
    4.  **Report Results**: Display $\Delta EVE$ values both in absolute terms and as a percentage of Tier 1 Capital.
    5.  **Visualize**: Present the $\Delta EVE$ results in an intuitive bar chart.
    6.  **Model Persistence**: Save the key model outputs and parameters for future reference or audit.
    """)

    # Check for prerequisites from previous pages
    if 'taiwan_portfolio_df' not in st.session_state or st.session_state['taiwan_portfolio_df'].empty:
        st.warning("Please go to 'Portfolio Generation' page and generate a portfolio first.")
        return
    if 'baseline_discount_curve_df' not in st.session_state or 'baseline_eve' not in st.session_state:
        st.warning("Please go to 'Cash Flow & Gap Analysis' page and run the analysis first.")
        return

    st.markdown("---")
    st.subheader("Run IRRBB Simulation")
    st.markdown("Click the button below to run the IRRBB simulation across all Basel shock scenarios and calculate $\Delta EVE$.")

    if st.button("Run IRRBB Simulation", help="Initiate the full IRRBB EVE simulation."):
        with st.spinner("Running IRRBB simulation across all scenarios... This may take a moment."):
            tier1_capital_val = st.session_state['tier1_capital']
            baseline_eve = st.session_state['baseline_eve']
            baseline_discount_curve_df = st.session_state['baseline_discount_curve_df']
            baseline_date_curve_df = st.session_state['baseline_date_curve_df']
            portfolio_df = st.session_state['taiwan_portfolio_df']
            
            mortgage_prepayment_rate_annual = st.session_state['mortgage_prepayment_rate_annual']
            nmd_beta = st.session_state['nmd_beta']
            nmd_behavioral_maturity_years = st.session_state['nmd_behavioral_maturity_years']
            behavioral_shock_adjustment_factor = st.session_state['behavioral_shock_adjustment_factor']

            shocked_eves = {}
            delta_eve_values = {}

            progress_bar = st.progress(0)
            status_text = st.empty()
            total_scenarios = len(shock_scenarios)

            for i, (scenario_name, shock_params) in enumerate(shock_scenarios.items()):
                status_text.text(f"Processing scenario: {scenario_name} ({i+1}/{total_scenarios})")
                progress_bar.progress((i + 1) / total_scenarios)

                shock_magnitude_bps_short = shock_params['short']
                shock_magnitude_bps_long = shock_params['long']

                # Generate shocked tenor curve
                shocked_tenor_curve = generate_basel_shocked_curve(
                    baseline_discount_curve_df, scenario_name,
                    shock_magnitude_bps_short, shock_magnitude_bps_long
                )
                # Convert to date curve for PV calculation
                shocked_date_curve = convert_tenor_curve_to_date_curve(shocked_tenor_curve, valuation_date)

                # Recalculate cash flows and PV under shock
                shocked_eve = recalculate_cashflows_and_pv_for_scenario(
                    portfolio_df,
                    shocked_date_curve,
                    valuation_date,
                    scenario_name,
                    baseline_date_curve_df, # Pass baseline_date_curve_df here
                    mortgage_prepayment_rate_annual,
                    behavioral_shock_adjustment_factor,
                    nmd_beta,
                    nmd_behavioral_maturity_years
                )
                shocked_eves[scenario_name] = shocked_eve

                delta_eve = calculate_delta_eve(baseline_eve, shocked_eve)
                delta_eve_values[scenario_name] = delta_eve
            
            st.session_state['shocked_eves'] = shocked_eves
            st.session_state['delta_eve_values'] = delta_eve_values
            
            delta_eve_report_df = report_delta_eve_as_percentage_of_tier1(
                delta_eve_values, tier1_capital_val
            )
            st.session_state['delta_eve_report_df'] = delta_eve_report_df
            st.success("IRRBB Simulation Complete!")

            # Persist model artifact
            model_artifact = {
                'valuation_date': valuation_date,
                'tier1_capital': tier1_capital_val,
                'baseline_eve': baseline_eve,
                'shocked_eves': shocked_eves,
                'delta_eve_report_df': delta_eve_report_df.to_dict('records') # Store as dict to easily recreate DF
            }
            save_model_artifact(model_artifact, "irrbb_gap_eve_model.pkl")
            st.success("Model artifact saved to irrbb_gap_eve_model.pkl.")

    st.markdown("---")
    st.subheader("Simulation Results")

    if 'baseline_eve' in st.session_state:
        st.markdown(f"**Baseline EVE:** {st.session_state['baseline_eve']:,.2f} TWD")
        st.markdown(f"**Total Instruments Analyzed:** {len(st.session_state['taiwan_portfolio_df'])}")
        st.markdown(f"**Scenarios Analyzed:** {len(shock_scenarios)}")
    
    if 'delta_eve_report_df' in st.session_state and not st.session_state['delta_eve_report_df'].empty:
        st.write("### Delta EVE Report (% of Tier 1 Capital)")
        st.dataframe(st.session_state['delta_eve_report_df'])
        
        plot_delta_eve_bar_chart(st.session_state['delta_eve_report_df'])

        st.download_button(
            label="Download Model Artifact (irrbb_gap_eve_model.pkl)",
            data=open("irrbb_gap_eve_model.pkl", "rb").read(),
            file_name="irrbb_gap_eve_model.pkl",
            mime="application/octet-stream",
            help="Download the saved IRRBB model results."
        )
    else:
        st.info("Run the simulation to see results.")


