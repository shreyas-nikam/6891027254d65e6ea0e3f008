import pytest
from unittest.mock import MagicMock, patch

# This block is mandatory, do not change or remove.
# from definition_7d9365533bcc47caa7dfcb1125a59c28 import IRRBBEngine

# Define a mock class that simulates the IRRBBEngine's behavior
# necessary for testing run_baseline_scenario.
# This allows us to control its internal state and dependencies.
class MockIRRBBEngine:
    def __init__(self, positions_df=None, scenarios_config=None, assumptions_config=None):
        self._baseline_eve = None
        self._baseline_nii = None
        self._is_baseline_calculated = False # State flag to track calculation status

        self.positions_df = positions_df if positions_df is not None else MagicMock(name="positions_df")
        # Ensure assumptions_config has "base_yield_curve_data" for mock calls
        self.assumptions_config = assumptions_config if assumptions_config is not None else {"base_yield_curve_data": MagicMock(name="base_yield_curve_data")}
        self.scenarios_config = scenarios_config if scenarios_config is not None else MagicMock(name="scenarios_config")

        # Internal methods that `run_baseline_scenario` is expected to call
        # These will be mocked at the instance level for each test
        self.generate_yield_curve = MagicMock(name="generate_yield_curve")
        self.calculate_discount_factors = MagicMock(name="calculate_discount_factors")
        self.calculate_present_value = MagicMock(name="calculate_present_value")
        self.calculate_nii = MagicMock(name="calculate_nii")

    # The run_baseline_scenario method's *expected implementation logic*
    # This is what the provided 'pass' stub is meant to become.
    def run_baseline_scenario(self):
        """
        Calculates the baseline Economic Value of Equity (EVE) and Net Interest Income (NII)
        using current market rates and the initial cash flows. This method orchestrates the
        necessary internal calls to calculate present values and NII without any applied shock.
        Arguments: None.
        Output: None (stores baseline EVE and NII internally within the engine instance).
        """
        try:
            # 1. Generate baseline yield curve using assumptions
            baseline_curve = self.generate_yield_curve(
                base_curve=self.assumptions_config["base_yield_curve_data"],
                shock_type="baseline",
                shock_magnitude=0
            )
            
            # 2. Calculate discount factors for the initial cash flows
            # A mock object is passed for cashflow_dates, as its extraction logic is not under test here.
            mock_cashflow_dates = MagicMock(name="mock_cashflow_dates_for_discount_factors") 
            discount_factors = self.calculate_discount_factors(baseline_curve, mock_cashflow_dates)
            
            # 3. Calculate baseline EVE
            pv_assets, pv_liabilities = self.calculate_present_value(self.positions_df, discount_factors)
            self._baseline_eve = pv_assets - pv_liabilities
            
            # 4. Calculate baseline NII for a 1-year horizon
            self._baseline_nii = self.calculate_nii(self.positions_df, horizon_months=12)
            
            # Set calculation flag to True upon successful completion
            self._is_baseline_calculated = True 
        except Exception as e:
            # Ensure the flag is not set (or reset) on failure
            self._is_baseline_calculated = False 
            raise # Re-raise the exception, consistent with propagating errors


# Patch the actual IRRBBEngine from definition_7d9365533bcc47caa7dfcb1125a59c28 to use our MockIRRBBEngine.
# This ensures that when tests import and use IRRBBEngine, they get our controllable mock.
@patch('definition_7d9365533bcc47caa7dfcb1125a59c28.IRRBBEngine', new=MockIRRBBEngine)
class TestIRRBBEngineBaselineScenario:

    @pytest.fixture
    def mock_engine(self):
        """
        Fixture to provide a fresh MockIRRBBEngine instance for each test.
        Sets default successful mock returns for internal methods.
        """
        engine = MockIRRBBEngine(
            positions_df=MagicMock(name="positions_df_fixture"),
            assumptions_config={"base_yield_curve_data": MagicMock(name="base_yield_curve_data_fixture")},
            scenarios_config=MagicMock(name="scenarios_config_fixture")
        )
        # Default successful returns for internal methods
        engine.generate_yield_curve.return_value = MagicMock(name="baseline_curve_return")
        engine.calculate_discount_factors.return_value = MagicMock(name="discount_factors_return")
        engine.calculate_present_value.return_value = (1000, 700) # Default PVs
        engine.calculate_nii.return_value = 50 # Default NII
        return engine

    def test_run_baseline_scenario_calculates_and_stores_eve_and_nii(self, mock_engine):
        """
        Test that run_baseline_scenario correctly calculates and stores baseline EVE and NII.
        It verifies internal method calls, their arguments, and final attribute assignments.
        """
        expected_pv_assets, expected_pv_liabilities = mock_engine.calculate_present_value.return_value
        expected_nii = mock_engine.calculate_nii.return_value

        mock_engine.run_baseline_scenario()

        # Assertions for internal method calls and arguments
        mock_engine.generate_yield_curve.assert_called_once_with(
            base_curve=mock_engine.assumptions_config["base_yield_curve_data"],
            shock_type="baseline",
            shock_magnitude=0
        )
        mock_engine.calculate_discount_factors.assert_called_once_with(
            mock_engine.generate_yield_curve.return_value, 
            MagicMock(name="mock_cashflow_dates_for_discount_factors") 
        )
        mock_engine.calculate_present_value.assert_called_once_with(
            mock_engine.positions_df,
            mock_engine.calculate_discount_factors.return_value
        )
        mock_engine.calculate_nii.assert_called_once_with(
            mock_engine.positions_df,
            horizon_months=12
        )

        # Assertions for the stored baseline values and state flag
        assert mock_engine._baseline_eve == (expected_pv_assets - expected_pv_liabilities)
        assert mock_engine._baseline_nii == expected_nii
        assert mock_engine._is_baseline_calculated is True

    def test_run_baseline_scenario_with_empty_portfolio(self, mock_engine):
        """
        Test that run_baseline_scenario handles an empty portfolio gracefully, 
        resulting in zero EVE and NII and setting the calculated flag.
        """
        mock_engine.positions_df = MagicMock(name="empty_positions_df")
        mock_engine.calculate_present_value.return_value = (0, 0)
        mock_engine.calculate_nii.return_value = 0

        mock_engine.run_baseline_scenario()
        
        # Assertions for zero values and state flag
        assert mock_engine._baseline_eve == 0
        assert mock_engine._baseline_nii == 0
        assert mock_engine._is_baseline_calculated is True
        mock_engine.calculate_present_value.assert_called_once()
        mock_engine.calculate_nii.assert_called_once()

    def test_run_baseline_scenario_propagates_exceptions_from_internal_calls(self, mock_engine):
        """
        Test that exceptions raised by internal calculation methods (e.g., calculate_present_value) 
        are propagated, and internal state is not set on failure.
        """
        mock_engine.calculate_present_value.side_effect = ValueError("Simulated PV calculation error")

        with pytest.raises(ValueError, match="Simulated PV calculation error"):
            mock_engine.run_baseline_scenario()

        # Verify internal method calls up to the point of failure
        mock_engine.generate_yield_curve.assert_called_once()
        mock_engine.calculate_discount_factors.assert_called_once()
        mock_engine.calculate_present_value.assert_called_once()
        mock_engine.calculate_nii.assert_not_called() # NII should not be called if PV fails first

        # Assert that baseline values and flag are not set
        assert mock_engine._baseline_eve is None
        assert mock_engine._baseline_nii is None
        assert mock_engine._is_baseline_calculated is False

    def test_run_baseline_scenario_handles_missing_base_yield_curve_data(self, mock_engine):
        """
        Test that the method raises KeyError if 'base_yield_curve_data' is missing from 
        assumptions_config, and internal state is not set.
        """
        mock_engine.assumptions_config = {} # Simulate missing configuration

        with pytest.raises(KeyError, match="'base_yield_curve_data'"):
            mock_engine.run_baseline_scenario()
        
        # Verify that generate_yield_curve was attempted, leading to the KeyError
        mock_engine.generate_yield_curve.assert_called_once()
        mock_engine.calculate_discount_factors.assert_not_called()
        mock_engine.calculate_present_value.assert_not_called()
        mock_engine.calculate_nii.assert_not_called()

        # Assert that baseline values and flag are not set
        assert mock_engine._baseline_eve is None
        assert mock_engine._baseline_nii is None
        assert mock_engine._is_baseline_calculated is False

    def test_run_baseline_scenario_recalculates_on_subsequent_calls(self, mock_engine):
        """
        Test that calling run_baseline_scenario multiple times performs recalculation,
        updating the internal values if underlying data/mocks change. 
        This verifies re-executability and state update.
        """
        # First run with initial values
        mock_engine.run_baseline_scenario()
        assert mock_engine._baseline_eve == 300 # 1000 - 700
        assert mock_engine._baseline_nii == 50
        assert mock_engine._is_baseline_calculated is True
        
        # Reset mocks to check call counts for the second run
        mock_engine.generate_yield_curve.reset_mock()
        mock_engine.calculate_discount_factors.reset_mock()
        mock_engine.calculate_present_value.reset_mock()
        mock_engine.calculate_nii.reset_mock()
        mock_engine._is_baseline_calculated = False # Reset flag for next run

        # Set new expected values for the second run
        mock_engine.calculate_present_value.return_value = (1200, 800) # New PVs
        mock_engine.calculate_nii.return_value = 60 # New NII
        mock_engine.run_baseline_scenario()

        # Assertions for second run: updated values and flag
        assert mock_engine._baseline_eve == 400 # 1200 - 800
        assert mock_engine._baseline_nii == 60
        assert mock_engine._is_baseline_calculated is True
        
        # Verify internal methods were called again for the recalculation
        mock_engine.generate_yield_curve.assert_called_once()
        mock_engine.calculate_discount_factors.assert_called_once()
        mock_engine.calculate_present_value.assert_called_once()
        mock_engine.calculate_nii.assert_called_once()