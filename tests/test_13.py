import pytest
import pandas as pd
from pandas.io.formats.style import Styler

from definition_9fa2da132be64217a124b7aa36d727c7 import display_scenario_results

def test_display_scenario_results_valid_input():
    """
    Test with valid data to ensure correct output type (Styler) and accurate percentage calculation.
    Covers expected positive and negative Delta EVE/NII values.
    """
    results_df = pd.DataFrame({
        'Scenario': ['Parallel Up', 'Parallel Down', 'Steepener'],
        'Delta EVE': [10000000, -5000000, 2500000],
        'Delta NII': [500000, -200000, 100000]
    })
    tier1_capital = 100000000 # 100 million TWD Tier-1 capital
    
    styled_result = display_scenario_results(results_df, tier1_capital)
    
    assert isinstance(styled_result, Styler)
    
    # Access the underlying DataFrame from the Styler object to check calculated values
    df_unwrapped = styled_result.data
    
    assert 'ΔEVE (% Tier-1)' in df_unwrapped.columns
    assert 'ΔNII (Year 1)' in df_unwrapped.columns
    assert len(df_unwrapped) == len(results_df)
    
    # Verify calculated percentage for the first scenario
    expected_eve_percent = (results_df.loc[0, 'Delta EVE'] / tier1_capital) * 100
    assert abs(df_unwrapped.loc[0, 'ΔEVE (% Tier-1)'] - expected_eve_percent) < 0.001
    
    # Verify calculated percentage for a negative Delta EVE
    expected_eve_percent_neg = (results_df.loc[1, 'Delta EVE'] / tier1_capital) * 100
    assert abs(df_unwrapped.loc[1, 'ΔEVE (% Tier-1)'] - expected_eve_percent_neg) < 0.001


def test_display_scenario_results_invalid_tier1_capital():
    """
    Test edge cases where tier1_capital is zero or negative.
    According to financial context, Tier-1 capital should be positive.
    Expects a ValueError for non-positive inputs.
    """
    results_df = pd.DataFrame({
        'Scenario': ['Parallel Up'],
        'Delta EVE': [10000000],
        'Delta NII': [500000]
    })
    
    # Test with zero tier1_capital
    with pytest.raises(ValueError, match="tier1_capital must be a positive number"):
        display_scenario_results(results_df, 0)
        
    # Test with negative tier1_capital
    with pytest.raises(ValueError, match="tier1_capital must be a positive number"):
        display_scenario_results(results_df, -100)

def test_display_scenario_results_empty_dataframe():
    """
    Test the function's behavior with an empty results_df DataFrame.
    It should return a Styler object without errors, representing an empty styled table.
    """
    results_df = pd.DataFrame(columns=['Scenario', 'Delta EVE', 'Delta NII'])
    tier1_capital = 100000000
    
    styled_result = display_scenario_results(results_df, tier1_capital)
    
    assert isinstance(styled_result, Styler)
    df_unwrapped = styled_result.data
    assert df_unwrapped.empty
    # Ensure the expected columns for display are still present even if empty
    assert 'ΔEVE (% Tier-1)' in df_unwrapped.columns
    assert 'ΔNII (Year 1)' in df_unwrapped.columns


def test_display_scenario_results_malformed_dataframe():
    """
    Test cases where the input results_df is missing essential columns
    or contains non-numeric data in columns required for calculation.
    Expects KeyError for missing columns and ValueError for non-numeric data.
    """
    tier1_capital = 100000000

    # Test with a missing required column ('Delta EVE' is misspelled)
    results_df_missing_col = pd.DataFrame({
        'Scenario': ['Parallel Up'],
        'Delta EVE_typo': [10000000], # Typo here
        'Delta NII': [500000]
    })
    with pytest.raises(KeyError, match="Input DataFrame must contain all required columns"):
        display_scenario_results(results_df_missing_col, tier1_capital)

    # Test with non-numeric data in a calculation column ('Delta EVE')
    results_df_non_numeric = pd.DataFrame({
        'Scenario': ['Parallel Up'],
        'Delta EVE': ['invalid_data'], # Non-numeric string
        'Delta NII': [500000]
    })
    with pytest.raises(ValueError, match="Columns 'Delta EVE' and 'Delta NII' must contain numeric data."):
        display_scenario_results(results_df_non_numeric, tier1_capital)


def test_display_scenario_results_invalid_input_types():
    """
    Test cases for incorrect data types passed to the function parameters.
    Expects TypeError for non-DataFrame results_df or non-numeric tier1_capital.
    """
    valid_df = pd.DataFrame({
        'Scenario': ['Up'], 'Delta EVE': [1], 'Delta NII': [1]
    })
    valid_capital = 100

    # Test results_df as None
    with pytest.raises(TypeError, match="results_df must be a pandas DataFrame."):
        display_scenario_results(None, valid_capital)

    # Test results_df as a list
    with pytest.raises(TypeError, match="results_df must be a pandas DataFrame."):
        display_scenario_results([1, 2, 3], valid_capital)

    # Test tier1_capital as a string
    with pytest.raises(TypeError, match="tier1_capital must be a numeric value"):
        display_scenario_results(valid_df, "not_a_number")
    
    # Test tier1_capital as None
    with pytest.raises(TypeError, match="tier1_capital must be a numeric value"):
        display_scenario_results(valid_df, None)

