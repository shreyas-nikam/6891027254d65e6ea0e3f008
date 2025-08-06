import pytest
import matplotlib.pyplot as plt # Required for patching
from definition_9381efd3229f43598fdb769087046090 import plot_eve_waterfall_chart

@pytest.mark.parametrize(
    "baseline_eve, scenario_eve, scenario_name, expected_exception",
    [
        # Test Case 1: Standard EVE increase (positive change)
        (1000.0, 1200.0, "Parallel Up (+200bp)", None),
        # Test Case 2: Standard EVE decrease (negative change)
        (1000.0, 800.0, "Parallel Down (-200bp)", None),
        # Test Case 3: No change in EVE (edge case)
        (500.0, 500.0, "No Change Scenario", None),
        # Test Case 4: Invalid type for baseline_eve (expect TypeError)
        ("invalid_float", 1200.0, "Invalid Baseline EVE", TypeError),
        # Test Case 5: Invalid type for scenario_name (expect TypeError)
        (1000.0, 1200.0, 123, TypeError),
    ]
)
def test_plot_eve_waterfall_chart(mocker, baseline_eve, scenario_eve, scenario_name, expected_exception):
    # Mock matplotlib.pyplot functions to prevent actual plotting and verify calls
    mock_plt_figure = mocker.patch('matplotlib.pyplot.figure')
    mock_plt_show = mocker.patch('matplotlib.pyplot.show')
    mock_plt_bar = mocker.patch('matplotlib.pyplot.bar')
    mock_plt_title = mocker.patch('matplotlib.pyplot.title')
    mock_plt_ylabel = mocker.patch('matplotlib.pyplot.ylabel')
    mock_plt_xticks = mocker.patch('matplotlib.pyplot.xticks')
    mock_plt_grid = mocker.patch('matplotlib.pyplot.grid')
    mock_plt_tight_layout = mocker.patch('matplotlib.pyplot.tight_layout')

    if expected_exception:
        # If an exception is expected, assert that it is raised
        with pytest.raises(expected_exception):
            plot_eve_waterfall_chart(baseline_eve, scenario_eve, scenario_name)
        
        # Ensure no plotting functions were called if an exception occurred due to invalid input
        mock_plt_figure.assert_not_called()
        mock_plt_show.assert_not_called()
        mock_plt_bar.assert_not_called()
        mock_plt_title.assert_not_called()
        mock_plt_ylabel.assert_not_called()
        mock_plt_xticks.assert_not_called()
        mock_plt_grid.assert_not_called()
        mock_plt_tight_layout.assert_not_called()
    else:
        # For valid inputs, the function should execute without raising an exception
        # and should call the relevant matplotlib functions.
        plot_eve_waterfall_chart(baseline_eve, scenario_eve, scenario_name)

        # Assert that core plotting functions were called at least once
        mock_plt_figure.assert_called_once()
        mock_plt_show.assert_called_once()
        # A waterfall chart typically uses plt.bar multiple times for segments
        mock_plt_bar.assert_called() 
        mock_plt_title.assert_called_once()
        mock_plt_ylabel.assert_called_once()
        mock_plt_xticks.assert_called_once()
        mock_plt_grid.assert_called_once()
        mock_plt_tight_layout.assert_called_once()