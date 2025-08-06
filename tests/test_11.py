import pytest
from definition_f6f6f2815a4f4f268705f05561db0eea import generate_yield_curves

@pytest.mark.parametrize(
    "baseline_params, expected_outcome",
    [
        # Test Case 1: Happy Path - Valid baseline parameters, check overall structure and baseline rates
        # Assumes the function returns a dict mapping tenor to rate for the curve.
        ({"tenors": [1.0, 5.0, 10.0], "rates": [0.01, 0.015, 0.02]}, 
         {"type": "success", "expected_baseline_rates": {1.0: 0.01, 5.0: 0.015, 10.0: 0.02}, "check_shock_scenario": None}),

        # Test Case 2: Edge Case - Empty baseline parameters
        # The function requires parameters to define the curve, so an empty dict should raise an error.
        ({}, 
         {"type": "error", "error_class": ValueError}),

        # Test Case 3: Edge Case - Invalid type for baseline parameters (e.g., list instead of dict)
        ([1, 2, 3], 
         {"type": "error", "error_class": TypeError}),
        
        # Test Case 4: Verify Parallel Up Shock Logic (200 bps shift up)
        ({"tenors": [1.0, 5.0, 10.0], "rates": [0.01, 0.015, 0.02]}, 
         {"type": "success", "expected_baseline_rates": None, "check_shock_scenario": {"Parallel Up": 0.02}}), # 0.02 = 200 basis points

        # Test Case 5: Verify Parallel Down Shock Logic with a rate floor at 0.0
        # Rates are low, so a -200bps shock will hit the floor.
        ({"tenors": [1.0, 5.0, 10.0], "rates": [0.005, 0.01, 0.015]}, # 50bp, 100bp, 150bp
         {"type": "success", "expected_baseline_rates": None, "check_shock_scenario": {"Parallel Down": -0.02}}) # -0.02 = -200 basis points
    ]
)
def test_generate_yield_curves(baseline_params, expected_outcome):
    """
    Tests the generate_yield_curves function for various inputs,
    including valid scenarios, invalid input types, and specific shock logic.
    """
    if expected_outcome["type"] == "error":
        with pytest.raises(expected_outcome["error_class"]):
            generate_yield_curves(baseline_params)
    else:
        baseline_curve, scenario_curves = generate_yield_curves(baseline_params)

        # Assertions common to all successful cases
        assert isinstance(baseline_curve, dict), "Baseline curve should be a dictionary."
        assert isinstance(scenario_curves, dict), "Scenario curves should be a dictionary."
        assert len(scenario_curves) == 6, "Expected 6 Basel-mandated scenario curves."

        expected_scenario_names = [
            "Parallel Up", "Parallel Down", "Steepener", "Flattener", "Short Up", "Short Down"
        ]
        for name in expected_scenario_names:
            assert name in scenario_curves, f"Missing expected scenario: {name}"
            assert isinstance(scenario_curves[name], dict), f"Scenario '{name}' curve should be a dictionary."
            # All scenario curves should have the same tenors as the baseline curve generated from params
            assert set(scenario_curves[name].keys()) == set(baseline_curve.keys()), \
                f"Tenors for '{name}' curve do not match baseline curve."

        # Specific assertion for Test Case 1: Check baseline curve values
        if expected_outcome.get("expected_baseline_rates"):
            for tenor, rate in expected_outcome["expected_baseline_rates"].items():
                assert tenor in baseline_curve, f"Tenor {tenor} not found in baseline curve."
                assert baseline_curve[tenor] == pytest.approx(rate), \
                    f"Baseline rate for tenor {tenor} does not match expected."

        # Specific assertions for Test Cases 4 & 5: Check shock logic
        if expected_outcome.get("check_shock_scenario"):
            for shock_name, shock_amount in expected_outcome["check_shock_scenario"].items():
                shocked_curve = scenario_curves.get(shock_name)
                assert shocked_curve is not None, f"Specific shock scenario '{shock_name}' curve not found."
                
                for tenor, baseline_rate in baseline_curve.items():
                    expected_rate = baseline_rate + shock_amount
                    
                    # Apply floor for interest rates, especially for Parallel Down shock
                    if shock_name == "Parallel Down":
                        # Interest rates typically do not go below zero, or a very small positive number (e.g., 1bp)
                        # Assuming a hard floor of 0.0 for this test.
                        expected_rate = max(0.0, expected_rate) 
                    
                    assert shocked_curve[tenor] == pytest.approx(expected_rate), \
                        f"{shock_name} curve rate for tenor {tenor} is incorrect."