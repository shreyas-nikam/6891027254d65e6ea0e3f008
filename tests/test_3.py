import pytest
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from unittest.mock import MagicMock

# Keep a placeholder definition_b3d77306ce73486e834c030d29921175 for the import of the module.
# Keep the `your_module` block as it is. DO NOT REPLACE or REMOVE the block.
from definition_b3d77306ce73486e834c030d29921175 import plot_balance_sheet_composition

# Mock matplotlib and seaborn to prevent actual plots from showing up and speed up tests
@pytest.fixture(autouse=True)
def no_plotting_output(monkeypatch):
    """Fixture to prevent actual plot display and mock plotting calls."""
    monkeypatch.setattr(plt, 'show', lambda: None)
    monkeypatch.setattr(sns, 'barplot', MagicMock())
    monkeypatch.setattr(plt, 'figure', MagicMock())
    monkeypatch.setattr(plt, 'title', MagicMock())
    monkeypatch.setattr(plt, 'xlabel', MagicMock())
    monkeypatch.setattr(plt, 'ylabel', MagicMock())
    monkeypatch.setattr(plt, 'xticks', MagicMock())
    monkeypatch.setattr(plt, 'legend', MagicMock())
    monkeypatch.setattr(plt, 'tight_layout', MagicMock())
    monkeypatch.setattr(plt, 'clf', MagicMock()) # Clear figure for clean state

@pytest.mark.parametrize("dataframe_input, expected_exception", [
    # Test Case 1: Valid DataFrame with typical data
    (pd.DataFrame({
        'instrument_type': ['Loan', 'Deposit', 'Bond', 'Mortgage', 'NMD'],
        'side': ['asset', 'liability', 'asset', 'asset', 'liability'],
        'notional_amt': [1000, 500, 2000, 1500, 700]
    }), None),
    # Test Case 2: Empty DataFrame but with all required columns
    (pd.DataFrame(columns=['instrument_type', 'side', 'notional_amt']), None),
    # Test Case 3: DataFrame missing a required column ('instrument_type')
    (pd.DataFrame({
        'side': ['asset', 'liability'],
        'notional_amt': [100, 200]
    }), KeyError),
    # Test Case 4: Invalid input type (not a pandas DataFrame)
    ("this_is_not_a_dataframe", AttributeError),
    # Test Case 5: 'notional_amt' column contains non-numeric data
    (pd.DataFrame({
        'instrument_type': ['Loan', 'Deposit'],
        'side': ['asset', 'liability'],
        'notional_amt': [1000, 'invalid_amount']
    }), (TypeError, ValueError)),
])
def test_plot_balance_sheet_composition(dataframe_input, expected_exception):
    """
    Tests the plot_balance_sheet_composition function with various inputs,
    covering expected functionality and edge cases.
    """
    if expected_exception is None:
        try:
            plot_balance_sheet_composition(dataframe_input)
            # For valid inputs, we expect no exception. Plotting calls are mocked.
            # We could add assertions here to check if sns.barplot.called, etc.
            # but per example, just checking for no exception is acceptable for success.
        except Exception as e:
            pytest.fail(f"plot_balance_sheet_composition raised an unexpected exception: {e}")
    else:
        # For error cases, assert that the expected exception is raised.
        with pytest.raises(expected_exception):
            plot_balance_sheet_composition(dataframe_input)