
import streamlit as st
from datetime import datetime
from irrbb_core_functions import generate_synthetic_portfolio, save_data_to_csv
from app import valuation_date # Import valuation_date

def run_page1():
    st.header("1. Portfolio Generation")
    st.markdown("""
    On this page, you can generate a synthetic banking book portfolio. 
    This portfolio will consist of various financial instruments like loans, deposits, and bonds, 
    each with unique characteristics such as rate type (fixed/floating), payment frequency, and maturity date.
    
    **Key parameters for portfolio generation:**
    *   **Number of Instruments**: Defines the total count of financial instruments in your synthetic portfolio.
    *   **Tier 1 Capital (TWD)**: Represents the bank's core capital, used as a basis for reporting $\Delta EVE$ as a percentage.
    *   **Portfolio Start Date**: The effective date from which the portfolio is considered active.
    *   **Portfolio End Date**: The latest possible maturity date for any instrument in the portfolio.
    
    The generated portfolio aims to mimic real-world banking book structures for a robust IRRBB analysis.
    """)

    with st.sidebar.expander("Portfolio Generation Parameters", expanded=True):
        num_instruments = st.number_input(
            "Number of Instruments",
            min_value=10,
            max_value=1000,
            value=25,
            step=1,
            help="Number of synthetic financial instruments to generate."
        )
        tier1_capital = st.number_input(
            "Tier 1 Capital (TWD)",
            min_value=100_000_000.0,
            max_value=100_000_000_000.0,
            value=1_000_000_000.0,
            step=100_000_000.0,
            format="%f",
            help="Bank's Tier 1 Capital in TWD. Used for percentage reporting of Delta EVE."
        )
        portfolio_start_date = st.date_input(
            "Portfolio Start Date",
            value=datetime(2023, 1, 1).date(),
            help="The effective start date for the generated portfolio."
        )
        portfolio_end_date = st.date_input(
            "Portfolio End Date",
            value=datetime(2050, 12, 31).date(),
            help="The latest possible maturity date for instruments in the portfolio."
        )
    
    st.session_state['num_instruments'] = num_instruments
    st.session_state['tier1_capital'] = tier1_capital
    st.session_state['portfolio_start_date'] = portfolio_start_date
    st.session_state['portfolio_end_date'] = portfolio_end_date

    # Initialize session state for portfolio if not exists or if parameters changed
    if 'taiwan_portfolio_df' not in st.session_state or \
       st.session_state.get('last_num_instruments') != num_instruments or \
       st.session_state.get('last_portfolio_start_date') != portfolio_start_date or \
       st.session_state.get('last_portfolio_end_date') != portfolio_end_date:
        
        st.session_state['taiwan_portfolio_df'] = generate_synthetic_portfolio(
            num_instruments, tier1_capital, portfolio_start_date, portfolio_end_date
        )
        st.session_state['last_num_instruments'] = num_instruments
        st.session_state['last_portfolio_start_date'] = portfolio_start_date
        st.session_state['last_portfolio_end_date'] = portfolio_end_date
        st.success("Synthetic Banking Book Portfolio Generated!")


    if 'taiwan_portfolio_df' in st.session_state and not st.session_state['taiwan_portfolio_df'].empty:
        st.subheader("Generated Synthetic Banking Book Portfolio (First 5 Rows)")
        st.dataframe(st.session_state['taiwan_portfolio_df'].head())

        st.markdown(f"**Total Instruments:** {len(st.session_state['taiwan_portfolio_df'])}")
        st.markdown(f"**Total Portfolio Balance:** {st.session_state['taiwan_portfolio_df']['balance'].sum():,.2f} TWD")
        st.markdown(f"**Tier 1 Capital:** {st.session_state['tier1_capital']:,.2f} TWD")

        st.download_button(
            label="Download Taiwan Portfolio as CSV",
            data=st.session_state['taiwan_portfolio_df'].to_csv(index=False).encode('utf-8'),
            file_name="Taiwan_Portfolio.csv",
            mime="text/csv",
            help="Download the generated synthetic portfolio data."
        )
    else:
        st.warning("Please adjust parameters and regenerate the portfolio.")



