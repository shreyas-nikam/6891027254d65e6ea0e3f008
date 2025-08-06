import pytest
import pandas as pd

# Keep the definition_093694b932d746f7a0b810988acfd7d3 block as it is. DO NOT REPLACE or REMOVE the block.
from definition_093694b932d746f7a0b810988acfd7d3 import IRRBBEngine # Assuming IRRBBEngine is the class under test
# End of definition_093694b932d746f7a0b810988acfd7d3 block


# --- Fixtures for mock data ---

@pytest.fixture
def mock_positions_df():
    """Returns a mock pandas DataFrame for positions, simulating pre-processed cash flows."""
    return pd.DataFrame({
        'instrument_id': [101, 102, 103],
        'notional': [1_000_000, 500_000, 2_000_000],
        'rate_type': ['Fixed', 'Floating', 'Fixed'],
        'maturity_date': pd.to_datetime(['2025-06-30', '2026-12-31', '2027-03-15']),
        'side': ['Asset', 'Liability', 'Asset']
    })

@pytest.fixture
def mock_empty_positions_df():
    """Returns an empty pandas DataFrame, simulating a valid but empty input."""
    return pd.DataFrame(columns=[
        'instrument_id', 'notional', 'rate_type', 'maturity_date', 'side'
    ])

@pytest.fixture
def mock_scenarios_config():
    """Returns a mock dictionary for scenarios configuration, as loaded from 'scenarios.yaml'."""
    return {
        'Parallel Up': {'shift_bps': 200, 'curve_points': [0.25, 0.5, 1, 2, 5, 10]},
        'Parallel Down': {'shift_bps': -200, 'curve_points': [0.25, 0.5, 1, 2, 5, 10]},
        'Steepener': {'short_shift_bps': -50, 'long_shift_bps': 50, 'pivot_tenor': 2}
    }

@pytest.fixture
def mock_assumptions_config():
    """Returns a mock dictionary for behavioral assumptions, as loaded from 'irrbb_assumptions.yaml'."""
    return {
        'discount_curve_basis': 'risk_free_plus_liquidity',
        'mortgage_prepayment_rate_annual': 0.05,
        'NMD_beta': 0.5,
        'tier1_capital': 100_000_000 # Example value based on specification
    }


# --- Test Cases ---

def test_irrbb_engine_init_valid_inputs(
    mock_positions_df, mock_scenarios_config, mock_assumptions_config
):
    """
    Test Case 1: Verify successful initialization with all valid and typical inputs.
    Checks if the `__init__` method correctly assigns the provided data to instance attributes.
    """
    engine = IRRBBEngine(mock_positions_df, mock_scenarios_config, mock_assumptions_config)

    assert engine.positions_df.equals(mock_positions_df)
    assert engine.scenarios_config == mock_scenarios_config
    assert engine.assumptions_config == mock_assumptions_config

def test_irrbb_engine_init_empty_positions_df(
    mock_empty_positions_df, mock_scenarios_config, mock_assumptions_config
):
    """
    Test Case 2: Edge Case - Verify initialization handles an empty pandas DataFrame for positions_df.
    The engine should store an empty DataFrame without raising an error, indicating robustness
    to valid but empty input data. Downstream methods would then handle the emptiness.
    """
    engine = IRRBBEngine(mock_empty_positions_df, mock_scenarios_config, mock_assumptions_config)

    assert engine.positions_df.empty
    assert engine.positions_df.equals(mock_empty_positions_df)
    assert engine.scenarios_config == mock_scenarios_config
    assert engine.assumptions_config == mock_assumptions_config

@pytest.mark.parametrize("invalid_df_input", [
    None,               # Test with None
    "not a dataframe",  # Test with a string
    123,                # Test with an integer
    [1, 2, 3],          # Test with a list
    {"key": "value"}    # Test with a dictionary
])
def test_irrbb_engine_init_invalid_positions_df_type(
    invalid_df_input, mock_scenarios_config, mock_assumptions_config
):
    """
    Test Case 3: Edge Case - Verify that TypeError is raised when positions_df is not a pandas DataFrame.
    This ensures basic input validation for the core data structure.
    """
    with pytest.raises(TypeError, match="positions_df must be a pandas DataFrame"):
        IRRBBEngine(invalid_df_input, mock_scenarios_config, mock_assumptions_config)

@pytest.mark.parametrize("invalid_config_input", [
    None,               # Test with None
    "not a dict",       # Test with a string
    123,                # Test with an integer
    [],                 # Test with a list
    pd.DataFrame()      # Test with a DataFrame
])
def test_irrbb_engine_init_invalid_scenarios_config_type(
    mock_positions_df, invalid_config_input, mock_assumptions_config
):
    """
    Test Case 4: Edge Case - Verify that TypeError is raised when scenarios_config is not a dictionary.
    This validates the type of the configuration input.
    """
    with pytest.raises(TypeError, match="scenarios_config must be a dictionary"):
        IRRBBEngine(mock_positions_df, invalid_config_input, mock_assumptions_config)

@pytest.mark.parametrize("invalid_config_input", [
    None,               # Test with None
    "not a dict",       # Test with a string
    123,                # Test with an integer
    [],                 # Test with a list
    pd.DataFrame()      # Test with a DataFrame
])
def test_irrbb_engine_init_invalid_assumptions_config_type(
    mock_positions_df, mock_scenarios_config, invalid_config_input
):
    """
    Test Case 5: Edge Case - Verify that TypeError is raised when assumptions_config is not a dictionary.
    This validates the type of the behavioral assumptions input.
    """
    with pytest.raises(TypeError, match="assumptions_config must be a dictionary"):
        IRRBBEngine(mock_positions_df, mock_scenarios_config, invalid_config_input)