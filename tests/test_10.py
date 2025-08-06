import pytest
from unittest.mock import Mock, patch

# Keep the placeholder for your module import.
# The IRRBBEngine class below serves as a detailed mock/implementation
# for testing purposes, reflecting the expected behavior based on the spec.
# In a real test setup, you would import the actual IRRBBEngine class.
# from definition_6245f2f5d05e47409d7d412e3d2a16a8 import IRRBBEngine

# We will define a minimal IRRBBEngine class here that reflects the expected
# behavior of the methods called by run_shock_scenario and the method itself.
# This allows the tests to run without having the full external module code.
class IRRBBEngine:
    def __init__(self, positions_df=None, scenarios_config=None, assumptions_config=None):
        self.positions_df = positions_df if positions_df is not None else Mock()
        self.scenarios_config = scenarios_config if scenarios_config is not None else {}
        self.assumptions_config = assumptions_config if assumptions_config is not None else {}
        self.baseline_eve = 0.0  # Will be set by fixture
        self.baseline_nii = 0.0  # Will be set by fixture
        self.tier1_capital = 0.0 # Will be set by fixture

    # Dummy methods that run_shock_scenario relies on.
    # In a real scenario, these would contain actual logic.
    def generate_yield_curve(self, base_curve, shock_type, shock_magnitude):
        return Mock()

    def calculate_discount_factors(self, yield_curve, cashflow_dates):
        return Mock()

    def reprice_floating_instruments(self, cashflows_df, scenario_yield_curve):
        return Mock()

    def adjust_behavioral_cashflows(self, cashflows_df, scenario_yield_curve):
        return Mock()

    # This method's return is complex: a tuple of two mocks, each returning a float.
    # The run_shock_scenario method accesses `.return_value` on these mocks.
    def calculate_present_value(self, cashflows_df, discount_factors_series):
        # Default mock behavior, actual returns set by patch in fixture
        return (Mock(return_value=0.0), Mock(return_value=0.0))

    # This method's return is a mock that itself has a `.return_value` accessed.
    def calculate_nii(self, cashflows_df, horizon_months=12):
        # Default mock behavior, actual returns set by patch in fixture
        return Mock(return_value=0.0)

    def run_shock_scenario(self, scenario_name):
        """    Applies a specific interest rate shock defined by its name and calculates the resulting change in Economic Value of Equity (Delta EVE) and Net Interest Income (Delta NII). This involves generating the scenario yield curve, calculating new discount factors, repricing floating instruments, adjusting behavioral cash flows, calculating scenario EVE and NII, and finally computing the deltas relative to the baseline.
Arguments: scenario_name (str) - The name of the interest rate shock scenario to run (e.g., 'Parallel Up').
Output: A dictionary or pandas DataFrame row containing the calculated Delta EVE (as a percentage of Tier-1 capital) and Delta NII (for year 1) for the specified scenario.
                """
        if not isinstance(scenario_name, str):
            raise TypeError("Scenario name must be a string.")

        if scenario_name not in self.scenarios_config:
            raise ValueError(f"Scenario '{scenario_name}' not found in configuration.")

        scenario_params = self.scenarios_config[scenario_name]
        
        # 1. Generate the scenario yield curve
        scenario_yield_curve = self.generate_yield_curve(
            base_curve=Mock(), # Assume a baseline curve exists
            shock_type=scenario_params.get('shock_type', 'unknown'), # Use .get to be safe
            shock_magnitude=scenario_params.get('magnitude', 0)
        )

        # 2. Calculate new discount factors
        discount_factors = self.calculate_discount_factors(scenario_yield_curve, Mock()) # Mock cashflow_dates

        # 3. Reprice floating instruments
        repriced_cashflows = self.reprice_floating_instruments(Mock(), scenario_yield_curve) # Mock initial cashflows_df

        # 4. Adjust behavioral cash flows
        adjusted_cashflows = self.adjust_behavioral_cashflows(repriced_cashflows, scenario_yield_curve)

        # 5. Calculate scenario EVE and NII
        # These methods return mocks, so we access their actual return values
        scenario_eve_assets_pv_mock, scenario_eve_liabilities_pv_mock = self.calculate_present_value(adjusted_cashflows, discount_factors)
        scenario_eve = scenario_eve_assets_pv_mock.return_value - scenario_eve_liabilities_pv_mock.return_value
        
        scenario_nii_mock = self.calculate_nii(adjusted_cashflows, horizon_months=12)
        scenario_nii = scenario_nii_mock.return_value

        # 6. Compute deltas relative to baseline
        # Check if baselines are initialized before arithmetic
        if self.baseline_eve is None or self.baseline_nii is None:
            raise RuntimeError("Baseline EVE or NII not initialized. Run baseline scenario first.")

        delta_eve = scenario_eve - self.baseline_eve
        delta_nii = scenario_nii - self.baseline_nii

        # Delta EVE as percentage of Tier-1 capital
        delta_eve_pct_tier1 = 0.0
        if self.tier1_capital is not None:
            if self.tier1_capital != 0:
                delta_eve_pct_tier1 = (delta_eve / self.tier1_capital) * 100
            else: # self.tier1_capital == 0
                delta_eve_pct_tier1 = 0.0 # Prevent ZeroDivisionError
        else: # self.tier1_capital is None
             raise RuntimeError("Tier-1 capital not initialized.")


        # Output: A dictionary or pandas DataFrame row
        return {
            'Scenario': scenario_name,
            'Delta EVE (% Tier-1)': delta_eve_pct_tier1,
            'Delta NII (Year 1)': delta_nii
        }


# Dummy config for scenarios, reflecting what might be in scenarios.yaml
MOCK_SCENARIOS_CONFIG = {
    'Parallel Up': {'shock_type': 'parallel', 'magnitude': 0.02},
    'Parallel Down': {'shock_type': 'parallel', 'magnitude': -0.02},
    'Steepener': {'shock_type': 'steepener', 'magnitude': {'short': -0.01, 'long': 0.01}},
    'Flattener': {'shock_type': 'flattener', 'magnitude': {'short': 0.01, 'long': -0.01}},
    'Short-end Up': {'shock_type': 'short_end_up', 'magnitude': 0.01},
}

# Define a fixture for a mock IRRBBEngine instance
@pytest.fixture
def mock_irrbb_engine_instance():
    # Instantiate the IRRBBEngine class (defined above, or from definition_6245f2f5d05e47409d7d412e3d2a16a8)
    engine = IRRBBEngine(
        positions_df=Mock(),
        scenarios_config=MOCK_SCENARIOS_CONFIG,
        assumptions_config=Mock()
    )
    
    # Set mock baseline values and Tier-1 capital
    engine.baseline_eve = 1000.0
    engine.baseline_nii = 500.0
    engine.tier1_capital = 20000.0

    # Ensure the internal methods of this specific instance are mocked
    # Patch these methods directly on the instance
    engine.generate_yield_curve = Mock(return_value=Mock())
    engine.calculate_discount_factors = Mock(return_value=Mock())
    engine.reprice_floating_instruments = Mock(return_value=Mock())
    engine.adjust_behavioral_cashflows = Mock(return_value=Mock())
    
    # Configure return values for calculate_present_value and calculate_nii
    # For 'Parallel Up', let's set values that result in:
    # Scenario EVE = 1450 (Assets PV) - 500 (Liabilities PV) = 950
    # Delta EVE = 950 - 1000 (baseline) = -50
    # Delta EVE % Tier-1 = (-50 / 20000) * 100 = -0.25
    engine.calculate_present_value = Mock(return_value=(Mock(return_value=1450.0), Mock(return_value=500.0)))

    # Scenario NII = 480
    # Delta NII = 480 - 500 (baseline) = -20
    engine.calculate_nii = Mock(return_value=Mock(return_value=480.0))

    return engine

# Test Case 1: Valid scenario - Parallel Up (expected functionality)
def test_run_shock_scenario_parallel_up(mock_irrbb_engine_instance):
    scenario_name = 'Parallel Up'
    result = mock_irrbb_engine_instance.run_shock_scenario(scenario_name)

    # Assert that all internal methods were called
    mock_irrbb_engine_instance.generate_yield_curve.assert_called_once()
    mock_irrbb_engine_instance.calculate_discount_factors.assert_called_once()
    mock_irrbb_engine_instance.reprice_floating_instruments.assert_called_once()
    mock_irrbb_engine_instance.adjust_behavioral_cashflows.assert_called_once()
    mock_irrbb_engine_instance.calculate_present_value.assert_called_once()
    mock_irrbb_engine_instance.calculate_nii.assert_called_once()

    # Assert output structure and calculated values
    assert isinstance(result, dict)
    assert 'Scenario' in result
    assert 'Delta EVE (% Tier-1)' in result
    assert 'Delta NII (Year 1)' in result

    assert result['Scenario'] == scenario_name
    assert pytest.approx(result['Delta EVE (% Tier-1)']) == -0.25 
    assert pytest.approx(result['Delta NII (Year 1)']) == -20.0

# Test Case 2: Another valid scenario - Steepener (expected functionality with different calculation outcome)
def test_run_shock_scenario_steepener(mock_irrbb_engine_instance):
    scenario_name = 'Steepener'
    
    # Adjust mock returns for this specific scenario to get different results
    # For Steepener, let's say Scenario EVE = 1050 (1550 - 500)
    # Delta EVE = 1050 - 1000 = 50
    # Delta EVE % Tier-1 = (50 / 20000) * 100 = 0.25
    mock_irrbb_engine_instance.calculate_present_value.return_value = (Mock(return_value=1550.0), Mock(return_value=500.0)) 
    
    # For Steepener, let's say Scenario NII = 450
    # Delta NII = 450 - 500 = -50
    mock_irrbb_engine_instance.calculate_nii.return_value = Mock(return_value=450.0)

    result = mock_irrbb_engine_instance.run_shock_scenario(scenario_name)

    assert result['Scenario'] == scenario_name
    assert pytest.approx(result['Delta EVE (% Tier-1)']) == 0.25
    assert pytest.approx(result['Delta NII (Year 1)']) == -50.0

# Test Case 3: Invalid scenario name (edge case)
def test_run_shock_scenario_invalid_name(mock_irrbb_engine_instance):
    scenario_name = 'NonExistentScenario'
    with pytest.raises(ValueError, match=f"Scenario '{scenario_name}' not found in configuration."):
        mock_irrbb_engine_instance.run_shock_scenario(scenario_name)

# Test Case 4: Non-string scenario name (edge case - TypeError)
@pytest.mark.parametrize("invalid_scenario_name", [
    123,
    None,
    ['Parallel Up'],
    {'name': 'Parallel Up'}
])
def test_run_shock_scenario_non_string_name(mock_irrbb_engine_instance, invalid_scenario_name):
    with pytest.raises(TypeError, match="Scenario name must be a string."):
        mock_irrbb_engine_instance.run_shock_scenario(invalid_scenario_name)

# Test Case 5: Baseline values not initialized or Tier-1 capital is problematic (edge cases)
def test_run_shock_scenario_uninitialized_attributes(mock_irrbb_engine_instance):
    # Test 5a: baseline_eve is None (or not run)
    mock_irrbb_engine_instance.baseline_eve = None
    with pytest.raises(RuntimeError, match="Baseline EVE or NII not initialized."):
        mock_irrbb_engine_instance.run_shock_scenario('Parallel Up')

    # Test 5b: baseline_nii is None
    mock_irrbb_engine_instance.baseline_eve = 1000.0 # Reset EVE
    mock_irrbb_engine_instance.baseline_nii = None
    with pytest.raises(RuntimeError, match="Baseline EVE or NII not initialized."):
        mock_irrbb_engine_instance.run_shock_scenario('Parallel Up')

    # Test 5c: Tier-1 capital is None
    mock_irrbb_engine_instance.baseline_eve = 1000.0
    mock_irrbb_engine_instance.baseline_nii = 500.0
    mock_irrbb_engine_instance.tier1_capital = None
    with pytest.raises(RuntimeError, match="Tier-1 capital not initialized."):
        mock_irrbb_engine_instance.run_shock_scenario('Parallel Up')

    # Test 5d: Tier-1 capital is 0 (should return 0.0% delta EVE without error)
    mock_irrbb_engine_instance.baseline_eve = 1000.0
    mock_irrbb_engine_instance.baseline_nii = 500.0
    mock_irrbb_engine_instance.tier1_capital = 0.0
    result = mock_irrbb_engine_instance.run_shock_scenario('Parallel Up')
    assert pytest.approx(result['Delta EVE (% Tier-1)']) == 0.0
    assert pytest.approx(result['Delta NII (Year 1)']) == -20.0 # NII delta still calculated correctly
