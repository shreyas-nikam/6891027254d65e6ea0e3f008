"""import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import uuid
import random


def run_portfolio_generation():
    st.header("Portfolio Generation")
    st.markdown("""This page allows you to generate a synthetic banking book portfolio.
    Adjust the parameters below to customize the portfolio.
    """)

    # Input widgets
    num_instruments = st.sidebar.number_input("Number of Instruments", min_value=1, value=25, step=1, help="The number of instruments to generate in the portfolio.")
    tier1_capital = st.sidebar.number_input("Tier 1 Capital (TWD)", min_value=1000000, value=1000000000, step=1000000, help="The Tier 1 Capital of the bank in TWD.")
    start_date = st.sidebar.date_input("Portfolio Start Date", value=datetime(2023, 1, 1), help="The start date of the portfolio.")
    end_date = st.sidebar.date_input("Portfolio End Date", value=datetime(2050, 12, 31), help="The end date of the portfolio.")

    if start_date >= end_date:
        st.error("Error: Portfolio Start Date must be before Portfolio End Date.")
        return

    if 'taiwan_portfolio_df' not in st.session_state:
        st.session_state['taiwan_portfolio_df'] = None

    if st.button("Generate Portfolio"):
        with st.spinner("Generating Portfolio..."):
            taiwan_portfolio_df = generate_synthetic_portfolio(
                num_instruments=num_instruments,
                tier1_capital=tier1_capital,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d")
            )
            st.session_state['taiwan_portfolio_df'] = taiwan_portfolio_df
            st.success("Portfolio Generated Successfully!")

    if st.session_state['taiwan_portfolio_df'] is not None:
        st.subheader("Generated Synthetic Banking Book Portfolio")
        st.dataframe(st.session_state['taiwan_portfolio_df'].head())
        st.markdown("Displaying the first few rows of the generated portfolio.")

        # Download button
        csv = st.session_state['taiwan_portfolio_df'].to_csv(index=False)
        st.download_button(
            label="Download Taiwan_Portfolio.csv",
            data=csv,
            file_name="Taiwan_Portfolio.csv",
            mime='text/csv',
        )


@st.cache_data # Cache the generated portfolio
def generate_synthetic_portfolio(num_instruments, tier1_capital, start_date, end_date):
    data = []
    portfolio_as_of_date = datetime.strptime(start_date, "%Y-%m-%d").strftime("%Y-%m-%d")

    for _ in range(num_instruments):
        instrument_id = uuid.uuid4()
        category = random.choice(['Asset', 'Liability'])
        balance = round(random.uniform(1000, 1000000), 2)
        rate_type = random.choice(['Fixed', 'Floating'])
        index = random.choice(['TAIBOR', 'Fixed']) if rate_type == 'Floating' else 'N/A'
        spread_bps = random.randint(0, 100) if rate_type == 'Floating' else 0
        current_rate = round(random.uniform(0.01, 0.05), 4)
        payment_freq = random.choice([1, 3, 6, 12])

        maturity_date = (datetime.strptime(portfolio_as_of_date, '%Y-%m-%d') + relativedelta(months=random.randint(12, 360))).strftime('%Y-%m-%d')
        next_repricing_date = (datetime.strptime(portfolio_as_of_date, '%Y-%m-%d') + relativedelta(months=random.randint(1, 12))) if rate_type == 'Floating' else 'N/A'

        currency = 'TWD'
        embedded_option = random.choice(['None', 'Prepayment', 'Call', 'Put'])
        is_core_NMD = random.choice([True, False]) if category == 'Liability' else False
        behavioral_flag = is_core_NMD  # only core NMDs have behavioral flag

        data.append({
            'instrument_id': instrument_id,
            'category': category,
            'balance': balance,
            'rate_type': rate_type,
            'index': index,
            'spread_bps': spread_bps,
            'current_rate': current_rate,
            'payment_freq': payment_freq,
            'maturity_date': maturity_date,
            'next_repricing_date': next_repricing_date,
            'currency': currency,
            'embedded_option': embedded_option,
            'is_core_NMD': is_core_NMD,
            'behavioral_flag': behavioral_flag
        })

    final_columns = [
        'instrument_id', 'category', 'balance', 'rate_type', 'index', 'spread_bps',
        'current_rate', 'payment_freq', 'maturity_date', 'next_repricing_date',
        'currency', 'embedded_option', 'is_core_NMD', 'behavioral_flag'
    ]
    df = pd.DataFrame(data).reindex(columns=final_columns)

    for col in ['maturity_date', 'next_repricing_date']:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: pd.to_datetime(x) if x != 'N/A' else None)

    return df

if __name__ == "__main__":
    run_portfolio_generation()""