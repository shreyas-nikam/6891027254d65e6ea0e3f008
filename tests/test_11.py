import pytest
import pandas as pd
from unittest.mock import MagicMock, patch

# Keep this placeholder block as it is
from definition_a7efc18c40d44d1fa4cf3157acf4a437 import IRRBBEngine


@patch('definition_a7efc18c40d44d1fa4cf3157acf4a437.IRRBBEngine.__init__', return_value=None)
def test_run_all_scenarios_standard_execution_and_structure(mock_init):
    """
    Test 1: Verify run_all_scenarios executes correctly for a standard set of scenarios,
    returns a pandas DataFrame, and that the DataFrame has the expected structure
    (correct number of rows and column names).
    """
    scenarios_config = {
        "Parallel Up": {}, "Parallel Down": {}, "Steepener": {},
        "Flattener": {}, "Short-end Up": {}, "Short-end Down": {}
    }
    
    # Create a dummy engine instance and set the attributes that run_all_scenarios depends on
    engine = IRRBBEngine(None, None, None) 
    engine.scenarios_config = scenarios_config
    engine.run_shock_scenario = MagicMock(return_value={
        'ΔEVE (% Tier-1)': -5.0,
        'ΔNII (Year 1)': -10_000_000
    })

    result_df = engine.run_all_scenarios()

    assert isinstance(result_df, pd.DataFrame)
    assert len(result_df) == len(scenarios_config)
    assert list(result_df.columns) == ['Scenario', 'ΔEVE (% Tier-1)', 'ΔNII (Year 1)']
    
    # Verify run_shock_scenario was called for each scenario
    assert engine.run_shock_scenario.call_count == len(scenarios_config)
    for scenario_name in scenarios_config.keys():
        engine.run_shock_scenario.assert_any_call(scenario_name)


@patch('definition_a7efc18c40d44d1fa4cf3157acf4a437.IRRBBEngine.__init__', return_value=None)
def test_run_all_scenarios_correct_aggregation_of_results(mock_init):
    """
    Test 2: Verify that run_all_scenarios correctly aggregates distinct results
    returned by run_shock_scenario into the final DataFrame.
    """
    scenarios_config = {
        "ScenarioA": {}, "ScenarioB": {}, "ScenarioC": {}
    }
    
    engine = IRRBBEngine(None, None, None)
    engine.scenarios_config = scenarios_config
    
    # Define distinct return values for each scenario
    mock_returns = {
        "ScenarioA": {'ΔEVE (% Tier-1)': -1.0, 'ΔNII (Year 1)': 100},
        "ScenarioB": {'ΔEVE (% Tier-1)': -2.0, 'ΔNII (Year 1)': 200},
        "ScenarioC": {'ΔEVE (% Tier-1)': -3.0, 'ΔNII (Year 1)': 300},
    }
    
    # Use side_effect to return different values based on the scenario name
    engine.run_shock_scenario = MagicMock(side_effect=lambda name: mock_returns[name])

    result_df = engine.run_all_scenarios()

    expected_df = pd.DataFrame([
        {'Scenario': 'ScenarioA', 'ΔEVE (% Tier-1)': -1.0, 'ΔNII (Year 1)': 100},
        {'Scenario': 'ScenarioB', 'ΔEVE (% Tier-1)': -2.0, 'ΔNII (Year 1)': 200},
        {'Scenario': 'ScenarioC', 'ΔEVE (% Tier-1)': -3.0, 'ΔNII (Year 1)': 300},
    ])
    
    pd.testing.assert_frame_equal(result_df, expected_df)
    assert engine.run_shock_scenario.call_count == len(scenarios_config)


@patch('definition_a7efc18c40d44d1fa4cf3157acf4a437.IRRBBEngine.__init__', return_value=None)
def test_run_all_scenarios_empty_scenario_config(mock_init):
    """
    Test 3: Verify run_all_scenarios handles an empty scenarios_config gracefully
    by returning an empty DataFrame with the correct columns.
    """
    scenarios_config = {} # Empty scenarios config
    
    engine = IRRBBEngine(None, None, None)
    engine.scenarios_config = scenarios_config
    engine.run_shock_scenario = MagicMock() # This mock should not be called

    result_df = engine.run_all_scenarios()

    assert isinstance(result_df, pd.DataFrame)
    assert result_df.empty
    assert list(result_df.columns) == ['Scenario', 'ΔEVE (% Tier-1)', 'ΔNII (Year 1)']
    engine.run_shock_scenario.assert_not_called()


@patch('definition_a7efc18c40d44d1fa4cf3157acf4a437.IRRBBEngine.__init__', return_value=None)
def test_run_all_scenarios_fewer_custom_scenarios(mock_init):
    """
    Test 4: Verify run_all_scenarios correctly processes and aggregates results
    when the scenario configuration contains a non-standard, smaller set of scenarios.
    """
    scenarios_config = {
        "CustomShock1": {},
        "CustomShock2": {"param": "value"}
    }
    
    engine = IRRBBEngine(None, None, None)
    engine.scenarios_config = scenarios_config
    
    mock_returns = {
        "CustomShock1": {'ΔEVE (% Tier-1)': -0.5, 'ΔNII (Year 1)': 50},
        "CustomShock2": {'ΔEVE (% Tier-1)': 0.5, 'ΔNII (Year 1)': -50},
    }
    engine.run_shock_scenario = MagicMock(side_effect=lambda name: mock_returns[name])

    result_df = engine.run_all_scenarios()

    assert isinstance(result_df, pd.DataFrame)
    assert len(result_df) == len(scenarios_config)
    expected_df = pd.DataFrame([
        {'Scenario': 'CustomShock1', 'ΔEVE (% Tier-1)': -0.5, 'ΔNII (Year 1)': 50},
        {'Scenario': 'CustomShock2', 'ΔEVE (% Tier-1)': 0.5, 'ΔNII (Year 1)': -50},
    ])
    
    pd.testing.assert_frame_equal(result_df, expected_df)
    assert engine.run_shock_scenario.call_count == len(scenarios_config)


@patch('definition_a7efc18c40d44d1fa4cf3157acf4a437.IRRBBEngine.__init__', return_value=None)
def test_run_all_scenarios_missing_keys_from_shock_result(mock_init):
    """
    Test 5: Verify run_all_scenarios handles cases where run_shock_scenario
    returns a dictionary with missing expected keys, by populating the DataFrame
    with NaN for those missing values.
    """
    scenarios_config = {
        "ScenarioWithMissingEVE": {},
        "ScenarioWithMissingNII": {},
        "ScenarioComplete": {}
    }
    
    engine = IRRBBEngine(None, None, None)
    engine.scenarios_config = scenarios_config
    
    # Mock `run_shock_scenario` to return dictionaries with varying completeness
    mock_returns = {
        "ScenarioWithMissingEVE": {'ΔNII (Year 1)': -15_000_000},
        "ScenarioWithMissingNII": {'ΔEVE (% Tier-1)': -7.0},
        "ScenarioComplete": {'ΔEVE (% Tier-1)': -1.0, 'ΔNII (Year 1)': 100},
    }
    engine.run_shock_scenario = MagicMock(side_effect=lambda name: mock_returns[name])

    result_df = engine.run_all_scenarios()

    assert isinstance(result_df, pd.DataFrame)
    assert len(result_df) == len(scenarios_config)
    assert list(result_df.columns) == ['Scenario', 'ΔEVE (% Tier-1)', 'ΔNII (Year 1)']
    
    expected_df = pd.DataFrame([
        {'Scenario': 'ScenarioWithMissingEVE', 'ΔEVE (% Tier-1)': float('nan'), 'ΔNII (Year 1)': -15_000_000.0},
        {'Scenario': 'ScenarioWithMissingNII', 'ΔEVE (% Tier-1)': -7.0, 'ΔNII (Year 1)': float('nan')},
        {'Scenario': 'ScenarioComplete', 'ΔEVE (% Tier-1)': -1.0, 'ΔNII (Year 1)': 100.0},
    ])
    
    # Ensure numerical columns are float to allow for NaN
    expected_df['ΔEVE (% Tier-1)'] = expected_df['ΔEVE (% Tier-1)'].astype(float)
    expected_df['ΔNII (Year 1)'] = expected_df['ΔNII (Year 1)'].astype(float)
    
    pd.testing.assert_frame_equal(result_df, expected_df)
    assert engine.run_shock_scenario.call_count == len(scenarios_config)