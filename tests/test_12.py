import pytest
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Placeholder for your module import
from definition_35947f1dbed547a9a97da2922d65ed50 import plot_gap_profile

# Define the expected Basel bucket order as mentioned in the specification
BASEL_BUCKET_ORDER = ['0-1M', '1-3M', '3-6M', '6-12M', '1-2Y', '2-3Y', '3-5Y', '5-10Y', '>10Y']

@pytest.fixture(autouse=True)
def mock_matplotlib(mocker):
    """
    Fixture to mock matplotlib.pyplot functions to prevent actual plot rendering
    and allow checking if plotting functions were called correctly.
    """
    mocker.patch('matplotlib.pyplot.show') 
    mocker.patch('matplotlib.pyplot.figure')
    mocker.patch('matplotlib.pyplot.bar')
    mocker.patch('matplotlib.pyplot.xlabel')
    mocker.patch('matplotlib.pyplot.ylabel')
    mocker.patch('matplotlib.pyplot.title')
    mocker.patch('matplotlib.pyplot.xticks')
    mocker.patch('matplotlib.pyplot.tight_layout')
    mocker.patch('matplotlib.pyplot.close') 

# Test Case 1: Successful plot generation with typical data and mixed cash flows
def test_plot_gap_profile_typical_data(mocker):
    """
    Tests if the function correctly processes a typical DataFrame with mixed
    inflows and outflows across various time buckets and calls matplotlib
    functions as expected.
    """
    cashflows_df = pd.DataFrame({
        'time_bucket': ['0-1M', '0-1M', '1-3M', '1-3M', '3-6M', '1-2Y', '3-5Y', '0-1M', '>10Y'],
        'amount': [100, -50, 200, -150, 300, 50, -20, 25, 1000] # Assuming 'amount' is already signed
    })
    
    plot_gap_profile(cashflows_df)

    # Assert that matplotlib functions were called as expected for plot generation
    plt.figure.assert_called_once()
    plt.bar.assert_called_once()
    plt.xlabel.assert_called_once_with('Time Buckets')
    plt.ylabel.assert_called_once_with('Net Gap (Inflows - Outflows)')
    plt.title.assert_called_once_with('Net Gap Profile by Time Bucket')
    plt.xticks.assert_called_once()
    plt.tight_layout.assert_called_once()
    plt.close.assert_called_once()

    # Verify the data passed to plt.bar
    args, _ = plt.bar.call_args
    plotted_buckets = list(args[0])
    plotted_gaps = list(args[1])

    # Calculate expected net gaps and sort according to BASEL_BUCKET_ORDER
    expected_grouped_data = cashflows_df.groupby('time_bucket')['amount'].sum()
    expected_buckets_sorted = [b for b in BASEL_BUCKET_ORDER if b in expected_grouped_data.index]
    expected_net_gaps_sorted = expected_grouped_data.reindex(expected_buckets_sorted).tolist()
    
    assert plotted_buckets == expected_buckets_sorted
    assert np.allclose(plotted_gaps, expected_net_gaps_sorted)

# Test Case 2: Empty DataFrame input
def test_plot_gap_profile_empty_dataframe(mocker):
    """
    Tests if the function handles an empty DataFrame gracefully without errors.
    It should still attempt to set up the plot but plot no bars.
    """
    cashflows_df = pd.DataFrame(columns=['time_bucket', 'amount']) 

    plot_gap_profile(cashflows_df)

    # A figure should still be created, and labels set
    plt.figure.assert_called_once()
    plt.xlabel.assert_called_once_with('Time Buckets')
    plt.ylabel.assert_called_once_with('Net Gap (Inflows - Outflows)')
    plt.title.assert_called_once_with('Net Gap Profile by Time Bucket')
    
    # Check if plt.bar was called with empty data (or not at all depending on implementation).
    # Most robust check is that it doesn't crash and closes the figure.
    if plt.bar.called:
        args, _ = plt.bar.call_args
        assert len(args[0]) == 0 and len(args[1]) == 0
    
    plt.tight_layout.assert_called_once()
    plt.close.assert_called_once()

# Test Case 3: DataFrame with missing required columns
def test_plot_gap_profile_missing_columns():
    """
    Tests if the function raises an appropriate error (KeyError) when critical
    columns like 'time_bucket' or 'amount' are missing.
    """
    # Missing 'amount' column
    cashflows_df_missing_amount = pd.DataFrame({
        'time_bucket': ['0-1M', '1-3M']
    })
    with pytest.raises(KeyError, match="amount"):
        plot_gap_profile(cashflows_df_missing_amount)

    # Missing 'time_bucket' column
    cashflows_df_missing_bucket = pd.DataFrame({
        'amount': [100, -50]
    })
    with pytest.raises(KeyError, match="time_bucket"):
        plot_gap_profile(cashflows_df_missing_bucket)

# Test Case 4: DataFrame with non-numeric data in amount column
def test_plot_gap_profile_non_numeric_amount():
    """
    Tests if the function correctly handles non-numeric data in the 'amount' column,
    expecting a TypeError or ValueError during aggregation.
    """
    cashflows_df = pd.DataFrame({
        'time_bucket': ['0-1M', '1-3M'],
        'amount': [100, 'invalid_value'] # Non-numeric data
    })
    
    # Pandas sum/aggregation on mixed types typically raises TypeError or ValueError
    with pytest.raises((TypeError, ValueError)): 
        plot_gap_profile(cashflows_df)

# Test Case 5: DataFrame with only positive or only negative cash flows (unidirectional gap)
def test_plot_gap_profile_unidirectional_cashflows(mocker):
    """
    Tests if the function correctly plots when all net gaps are either positive (inflows)
    or negative (outflows), ensuring the plotting logic handles single-sided data.
    """
    # Only positive amounts (net positive gap for all buckets)
    cashflows_df_inflows = pd.DataFrame({
        'time_bucket': ['0-1M', '1-3M', '3-6M'],
        'amount': [100, 200, 300]
    })

    plot_gap_profile(cashflows_df_inflows)
    plt.bar.assert_called_once()
    args_in, _ = plt.bar.call_args
    expected_grouped_data_in = cashflows_df_inflows.groupby('time_bucket')['amount'].sum()
    expected_buckets_in_sorted = [b for b in BASEL_BUCKET_ORDER if b in expected_grouped_data_in.index]
    expected_net_gaps_in_sorted = expected_grouped_data_in.reindex(expected_buckets_in_sorted).tolist()
    assert list(args_in[0]) == expected_buckets_in_sorted
    assert np.allclose(list(args_in[1]), expected_net_gaps_in_sorted)
    plt.close.assert_called_once()
    
    # Reset mocks to check the next call independently
    mocker.resetall() 
    mock_matplotlib(mocker) # Reapply the mock setup

    # Only negative amounts (net negative gap for all buckets)
    cashflows_df_outflows = pd.DataFrame({
        'time_bucket': ['0-1M', '1-3M', '3-6M'],
        'amount': [-100, -200, -300]
    })

    plot_gap_profile(cashflows_df_outflows)
    plt.bar.assert_called_once()
    args_out, _ = plt.bar.call_args
    expected_grouped_data_out = cashflows_df_outflows.groupby('time_bucket')['amount'].sum()
    expected_buckets_out_sorted = [b for b in BASEL_BUCKET_ORDER if b in expected_grouped_data_out.index]
    expected_net_gaps_out_sorted = expected_grouped_data_out.reindex(expected_buckets_out_sorted).tolist()
    assert list(args_out[0]) == expected_buckets_out_sorted
    assert np.allclose(list(args_out[1]), expected_net_gaps_out_sorted)
    plt.close.assert_called_once()