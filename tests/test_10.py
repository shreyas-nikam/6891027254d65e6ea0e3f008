import pytest
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns 

from definition_0bfca3009c0b4d8497d6e40a31acc846 import plot_partial_pv01_term_structure

@pytest.mark.parametrize("gap_table_dataframe, expected_exception", [
    # Test Case 1: Valid DataFrame with diverse PV01 values and standard Basel buckets.
    # This covers the expected functional input, ensuring plotting proceeds without error.
    (pd.DataFrame({'PV01': [100.5, -50.2, 200.0, 10.1, -5.3, 30.0, -15.0, 75.0, 120.0]}, 
                   index=['0-1M', '1-3M', '3-6M', '6-12M', '1-2Y', '2-3Y', '3-5Y', '5-10Y', '>10Y']), 
     None),
    # Test Case 2: Empty DataFrame. The function should ideally handle this gracefully by
    # displaying an empty plot (e.g., axes without data points) without raising an error.
    (pd.DataFrame(columns=['PV01']), 
     None), 
    # Test Case 3: DataFrame with all zero PV01s. Should plot a flat line at zero,
    # verifying behavior when PV01 values are neutral.
    (pd.DataFrame({'PV01': [0.0, 0.0, 0.0, 0.0]}, 
                   index=['BucketA', 'BucketB', 'BucketC', 'BucketD']), 
     None),
    # Test Case 4: DataFrame missing the crucial 'PV01' column. This is an edge case
    # where required data for plotting is absent. It should raise a KeyError as the function
    # attempts to access a non-existent column.
    (pd.DataFrame({'Net Gap': [10, 20, 30]}, index=['0-1M', '1-3M', '3-6M']), 
     KeyError),
    # Test Case 5: DataFrame with non-numeric data in the 'PV01' column.
    # Plotting libraries (like Matplotlib/Seaborn) expect numeric data for plotting.
    # Passing non-numeric values should lead to a ValueError during the plotting attempt.
    (pd.DataFrame({'PV01': ['abc', 'def', '123_invalid']}, index=['X', 'Y', 'Z']), 
     ValueError), 
])
def test_plot_partial_pv01_term_structure(gap_table_dataframe, expected_exception, mocker):
    # Mock matplotlib.pyplot.show to prevent actual plot display during tests
    # and to verify that the plotting function successfully completed its execution path.
    mock_plt_show = mocker.patch('matplotlib.pyplot.show')
    # Mock seaborn.lineplot as the function is expected to generate a "seaborn line plot".
    # This verifies that the core plotting function within seaborn was called.
    mock_sns_lineplot = mocker.patch('seaborn.lineplot')

    try:
        # Call the function under test
        plot_partial_pv01_term_structure(gap_table_dataframe)
        
        # If execution reaches this point, no exception was raised.
        # Assert that no exception was expected for this input, confirming success path.
        assert expected_exception is None 
        
        # For successful plotting, plt.show() should always be called.
        mock_plt_show.assert_called_once()
        # For successful plotting, sns.lineplot should also be called to prepare the plot.
        # This holds true even for empty dataframes or all-zero dataframes as axes are still set up.
        mock_sns_lineplot.assert_called_once()

    except Exception as e:
        # If an exception was caught during the function call,
        # assert that the raised exception matches the expected type.
        assert isinstance(e, expected_exception)
        # If an exception occurred, no plotting calls (show or lineplot) should have been made.
        mock_plt_show.assert_not_called()
        mock_sns_lineplot.assert_not_called()