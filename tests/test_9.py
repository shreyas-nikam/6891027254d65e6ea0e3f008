import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

# Keep a placeholder definition_28efa080edf441b5a4bec91213ce7738 for the import of the module. Keep the `your_module` block as it is. DO NOT REPLACE or REMOVE the block.
from definition_28efa080edf441b5a4bec91213ce7738 import plot_gap_table_heatmap

@pytest.fixture
def mock_plotting_libs():
    """Mocks seaborn and matplotlib.pyplot to prevent actual plotting."""
    with patch('seaborn.heatmap') as mock_heatmap, \
         patch('matplotlib.pyplot.show') as mock_show, \
         patch('matplotlib.pyplot.title') as mock_title, \
         patch('matplotlib.pyplot.xlabel') as mock_xlabel, \
         patch('matplotlib.pyplot.ylabel') as mock_ylabel:
        yield mock_heatmap, mock_show, mock_title, mock_xlabel, mock_ylabel

def test_plot_gap_table_heatmap_valid_data(mock_plotting_libs):
    """Test with a valid, typical gap table DataFrame, ensuring plotting functions are called."""
    mock_heatmap, mock_show, mock_title, mock_xlabel, mock_ylabel = mock_plotting_libs

    data = {
        '0-1M': [100, 80, 20],
        '1-3M': [200, 220, -20],
        '3-6M': [150, 100, 50]
    }
    # Index should represent rows, e.g., 'Assets', 'Liabilities', 'Net Gap'
    df = pd.DataFrame(data, index=['Assets', 'Liabilities', 'Net Gap'])

    result = plot_gap_table_heatmap(df)

    assert result is None
    mock_heatmap.assert_called_once()
    # Verify heatmap was called with the correct DataFrame
    pd.testing.assert_frame_equal(mock_heatmap.call_args[0][0], df)
    mock_title.assert_called_once_with("Gap Table Heatmap: Repricing Mismatches Across Basel Buckets")
    # Asserting xlabel/ylabel based on common heatmap interpretation, assuming they are set
    mock_xlabel.assert_called_once_with("Time Buckets") 
    mock_ylabel.assert_called_once_with("Instrument Type / Gap Metric")
    mock_show.assert_called_once()

def test_plot_gap_table_heatmap_empty_dataframe(mock_plotting_libs):
    """Test with an empty DataFrame, expecting no error and plotting functions to be called."""
    mock_heatmap, mock_show, _, _, _ = mock_plotting_libs

    df_empty = pd.DataFrame()

    result = plot_gap_table_heatmap(df_empty)

    assert result is None
    # Seaborn's heatmap generally handles empty DataFrames without error, producing an empty plot.
    mock_heatmap.assert_called_once()
    pd.testing.assert_frame_equal(mock_heatmap.call_args[0][0], df_empty)
    mock_show.assert_called_once()

def test_plot_gap_table_heatmap_non_numeric_data():
    """Test with a DataFrame containing non-numeric data, expecting an error from plotting library."""
    data = {
        '0-1M': [100, 80, 'invalid'], # 'invalid' is non-numeric
        '1-3M': [200, 220, -20]
    }
    df_non_numeric = pd.DataFrame(data, index=['Assets', 'Liabilities', 'Net Gap'])

    with pytest.raises(Exception) as excinfo:
        plot_gap_table_heatmap(df_non_numeric)
    
    # Expecting an error from pandas/seaborn when trying to process non-numeric data for heatmap
    # Common errors are TypeError or ValueError related to data conversion.
    assert isinstance(excinfo.value, (TypeError, ValueError))
    # A more specific message check could be added if the exact error signature from the
    # internal implementation (via seaborn) is known, e.g., "could not convert string to float"

@pytest.mark.parametrize("invalid_input", [
    None,
    [1, 2, 3],
    "not a dataframe",
    123,
    {'key': 'value'}
])
def test_plot_gap_table_heatmap_invalid_input_type(invalid_input):
    """Test with non-DataFrame inputs, expecting a TypeError."""
    with pytest.raises(TypeError):
        plot_gap_table_heatmap(invalid_input)

def test_plot_gap_table_heatmap_single_cell_dataframe(mock_plotting_libs):
    """Test with a DataFrame containing only a single cell, ensuring it's handled."""
    mock_heatmap, mock_show, _, _, _ = mock_plotting_libs

    df_single_cell = pd.DataFrame({'Value': [100]}, index=['Single'])

    result = plot_gap_table_heatmap(df_single_cell)

    assert result is None
    mock_heatmap.assert_called_once()
    pd.testing.assert_frame_equal(mock_heatmap.call_args[0][0], df_single_cell)
    mock_show.assert_called_once()
