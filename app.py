
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import uuid
from scipy.interpolate import interp1d
import plotly.express as px # Using Plotly as required
import plotly.graph_objects as go
import pickle
import random

st.set_page_config(page_title="QuLab", layout="wide")
st.sidebar.image("https://www.quantuniversity.com/assets/img/logo5.jpg")
st.sidebar.divider()
st.title("QuLab")
st.divider()
st.markdown("""
In this lab, we will develop a comprehensive Interest Rate Risk in the Banking Book (IRRBB) engine. This application provides a full-revaluation framework to analyze the impact of interest rate changes on a bank's Economic Value of Equity (EVE). Users can simulate a synthetic banking book portfolio, generate cash flows, apply various Basel interest rate shock scenarios, and quantify the resulting $\Delta EVE$.

### Learning Goals

Upon using this application, you will be able to:
*   Assemble a banking-book positions dataset that captures interest-sensitive assets, liabilities, and (optionally) simple hedges.
*   Generate synthetic cash-flow data for those positions, respecting product features and behavioural assumptions.
*   Build a full-revaluation IRRBB engine that computes baseline present values, allocates cash flows into regulatory time buckets, and estimates $\Delta EVE$ under the Basel six-scenario shock set.
*   Report $\Delta EVE$ as a percentage of Tier 1 capital and interpret the risk signal of each scenario.

### Mathematical Foundations for EVE

The Present Value (PV) of a series of cash flows is the sum of the present values of each individual cash flow. For a single cash flow $CF_t$ received at time $t$, discounted at a rate $r_t$: 
$$ PV(CF_t) = \frac{CF_t}{(1 + r_t)^{t}} $$
For a series of cash flows $CF_1, CF_2, \ldots, CF_M$ occurring at times $t_1, t_2, \ldots, t_M$: 
$$ PV = \sum_{k=1}^{M} \frac{CF_k}{(1 + r_{t_k})^{t_k}} $$
For EVE calculation, the cash flows will be discounted using a risk-free yield curve plus an appropriate liquidity spread; commercial margins are excluded.

EVE is defined as the present value of all banking book assets minus the present value of all banking book liabilities and off-balance sheet items:
$$ EVE_{\text{baseline}} = \sum_{i=1}^{N_A} PV(CF_{A,i}) - \sum_{j=1}^{N_L} PV(CF_{L,j}) $$

$\Delta EVE$ measures the change in a bank's EVE due to an interest rate shock:
$$ \Delta EVE = EVE_{\text{shocked}} - EVE_{\text{baseline}} $$

$\Delta EVE$ will be reported as a percentage of Tier 1 capital, allowing for a standardized interpretation of the risk signal:
$$ \Delta EVE (\% \text{ Tier 1 Capital}) = \frac{\Delta EVE}{\text{Tier 1 Capital}} \times 100\% $$

The net gap for each time bucket represents the difference between total cash inflows (from assets) and total cash outflows (from liabilities and derivatives) within that bucket:
$$ Net\ Gap_{\text{bucket } k} = \sum_{\text{assets in bucket } k} CF_{\text{in}} - \sum_{\text{liabilities in bucket } k} CF_{\text{out}} $$

"""
)

# Global Constants/Parameters
# Define standard Basel buckets for tenors (in months)
standard_tenors_months = [
    1, 3, 6, 12, 24, 36, 60, 120, 180, 240, 360 # Corresponding to 1M, 3M, 6M, 1Y, 2Y, 3Y, 5Y, 10Y, 15Y, 20Y, 30Y
]

# Market rates for baseline discount curve (fixed for this application)
market_rates_data = {
    '1M': 0.02, '3M': 0.022, '6M': 0.025, '1Y': 0.028, '2Y': 0.03, '3Y': 0.032,
    '5Y': 0.035, '7Y': 0.037, '10Y': 0.04, '15Y': 0.042, '20Y': 0.043, '30Y': 0.044
}

# Basel bucket definitions for gap analysis
basel_bucket_definitions_list = [
    (0, 1, 'M'), (1, 3, 'M'), (3, 6, 'M'), (6, 12, 'M'),
    (1, 2, 'Y'), (2, 3, 'Y'), (3, 5, 'Y'), (5, 10, 'Y'), (10, float('inf'), 'Y')
]

# Shock scenarios definitions (fixed for this application)
shock_scenarios = {
    'Parallel Up': {'short': 200, 'long': 200},  # +200 bps across the curve
    'Parallel Down': {'short': -200, 'long': -200},  # -200 bps across the curve
    'Steepener': {'short': -100, 'long': 100},  # Short rates down 100 bps, long rates up 100 bps
    'Flattener': {'short': 100, 'long': -100},  # Short rates up 100 bps, long rates down 100 bps
    'Short-Up': {'short': 200, 'long': 0},  # Short rates up 200 bps, long unchanged
    'Short-Down': {'short': -200, 'long': 0}  # Short rates down 200 bps, long unchanged
}

# Utility Functions
def save_data_to_csv(dataframe, filename):
    dataframe.to_csv(filename, index=False)

def save_data_to_parquet(dataframe, filename):
    dataframe.to_parquet(filename, index=False)

def save_model_artifact(model_object, filename):
    with open(filename, 'wb') as f:
        pickle.dump(model_object, f)

def plot_delta_eve_bar_chart(delta_eve_percentages):
    fig = px.bar(
        delta_eve_percentages,
        x='Scenario',
        y='Delta EVE (% Tier 1 Capital)',
        color='Scenario',
        title='Delta EVE by Basel Interest Rate Shock Scenario',
        labels={'Delta EVE (% Tier 1 Capital)': 'Delta EVE (% of Tier 1 Capital)'},
        color_discrete_sequence=px.colors.viridis.qualitative
    )
    fig.update_layout(
        xaxis_title='Scenario',
        yaxis_title='Delta EVE (% of Tier 1 Capital)',
        xaxis_tickangle=-45,
        bargap=0.2, # gap between bars of adjacent location coordinates.
    )
    fig.update_yaxes(gridcolor='lightgray', showgrid=True)
    st.plotly_chart(fig, use_container_width=True)

def convert_tenor_curve_to_date_curve(tenor_curve_df, valuation_date_for_conversion):
    date_curve_data = []
    for index, row in tenor_curve_df.iterrows():
        tenor_months = row['Tenor_Months']
        rate = row['Discount_Rate']
        target_date = valuation_date_for_conversion + relativedelta(months=tenor_months)
        date_curve_data.append({'date': target_date, 'rate': rate})
    return pd.DataFrame(date_curve_data)

# Your code starts here
page = st.sidebar.selectbox(label="Navigation", options=["Portfolio Generation", "Cash Flow & Gap Analysis", "IRRBB Simulation Results"])

if page == "Portfolio Generation":
    from application_pages.page1 import run_page1
    run_page1()
elif page == "Cash Flow & Gap Analysis":
    from application_pages.page2 import run_page2
    run_page2()
elif page == "IRRBB Simulation Results":
    from application_pages.page3 import run_page3
    run_page3()
# Your code ends
