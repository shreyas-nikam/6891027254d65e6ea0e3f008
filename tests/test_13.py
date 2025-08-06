import pytest
import io
import sys
from definition_0a4c423203a44c3996ef981d692b1a7d import display_scenario_results_table

# Define the expected Basel scenarios for consistent testing
# Based on the notebook specification section 2.8
BASEL_SCENARIOS = [
    "Parallel Up",
    "Parallel Down",
    "Steepener",
    "Flattener",
    "Short Rate Up",
    "Short Rate Down",
]

@pytest.fixture
def capture_stdout(capfd):
    """Fixture to capture stdout and stderr."""
    yield capfd

def test_display_scenario_results_table_full_valid_data(capture_stdout):
    """
    Test case 1: Verify the function correctly displays a full table with valid data.
    Checks for headers, correct percentage calculation (assuming 2 decimal places),
    and presence of all expected scenarios and their corresponding NII values.
    """
    delta_eve_results = {
        "Parallel Up": -500000.0,
        "Parallel Down": 350000.0,
        "Steepener": -100000.0,
        "Flattener": 80000.0,
        "Short Rate Up": -200000.0,
        "Short Rate Down": 150000.0,
    }
    delta_nii_results = {
        "Parallel Up": {"1Y": -10000.0, "3Y": -25000.0},
        "Parallel Down": {"1Y": 7500.0, "3Y": 18000.0},
        "Steepener": {"1Y": -2000.0, "3Y": -5000.0},
        "Flattener": {"1Y": 1500.0, "3Y": 4000.0},
        "Short Rate Up": {"1Y": -4000.0, "3Y": -10000.0},
        "Short Rate Down": {"1Y": 3000.0, "3Y": 7500.0},
    }
    tier1_capital = 10_000_000.0

    display_scenario_results_table(delta_eve_results, delta_nii_results, tier1_capital)

    out, err = capture_stdout.readouterr()

    assert err == "", "Stderr should be empty"

    # Check for table headers
    assert "Scenario" in out
    assert "Delta EVE (% of T1)" in out
    assert "Delta NII (1-Year)" in out
    assert "Delta NII (3-Year)" in out

    # Check for content of specific rows (assuming basic formatting for numbers)
    # Delta EVE (% of T1) calculations:
    # Parallel Up: (-500000 / 10,000,000) * 100 = -5.00
    # Parallel Down: (350000 / 10,000,000) * 100 = 3.50
    assert "Parallel Up" in out and "-5.00 %" in out
    assert "Parallel Down" in out and "3.50 %" in out
    assert "Steepener" in out and "-1.00 %" in out # (-100000/10M)*100
    assert "Flattener" in out and "0.80 %" in out # (80000/10M)*100
    assert "Short Rate Up" in out and "-2.00 %" in out # (-200000/10M)*100
    assert "Short Rate Down" in out and "1.50 %" in out # (150000/10M)*100

    # Check for NII values (allowing for common formatting variations like commas)
    assert "Parallel Up" in out and ("-10,000.00" in out or "-10000.00" in out) and ("-25,000.00" in out or "-25000.00" in out)
    assert "Parallel Down" in out and ("7,500.00" in out or "7500.00" in out) and ("18,000.00" in out or "18000.00" in out)


def test_display_scenario_results_table_empty_inputs(capture_stdout):
    """
    Test case 2: Verify graceful handling when delta results dictionaries are empty.
    The table should display headers but no data rows.
    """
    delta_eve_results = {}
    delta_nii_results = {}
    tier1_capital = 1_000_000.0

    display_scenario_results_table(delta_eve_results, delta_nii_results, tier1_capital)

    out, err = capture_stdout.readouterr()

    assert err == "", "Stderr should be empty"
    # Check for table headers
    assert "Scenario" in out
    assert "Delta EVE (% of T1)" in out
    assert "Delta NII (1-Year)" in out
    assert "Delta NII (3-Year)" in out

    # Ensure no scenario data rows are present in the output
    for scenario in BASEL_SCENARIOS:
        assert scenario not in out, f"Unexpected scenario '{scenario}' found in output."
    # Further check for absence of numerical data patterns
    import re
    assert not re.search(r'\d+\.\d+\s%', out) # No percentages
    assert not re.search(r'[-]?\d{1,3}(?:,\d{3})*\.\d{2}', out) # No formatted numbers


def test_display_scenario_results_table_zero_tier1_capital(capture_stdout):
    """
    Test case 3: Verify handling when Tier 1 capital is zero.
    The Delta EVE (% of T1) should display as 'N/A', 'Inf', or 'nan' due to division by zero.
    Other values (NII) should still display normally.
    """
    delta_eve_results = {
        "Parallel Up": -500000.0,
        "Short Rate Down": 150000.0,
    }
    delta_nii_results = {
        "Parallel Up": {"1Y": -10000.0, "3Y": -25000.0},
        "Short Rate Down": {"1Y": 3000.0, "3Y": 7500.0},
    }
    tier1_capital = 0.0

    display_scenario_results_table(delta_eve_results, delta_nii_results, tier1_capital)

    out, err = capture_stdout.readouterr()

    assert err == "", "Stderr should be empty"
    assert "Scenario" in out
    assert "Delta EVE (% of T1)" in out
    assert "Delta NII (1-Year)" in out

    # Check that 'N/A', 'Inf', or 'nan' is displayed for the percentage.
    # The actual output might vary depending on the implementation's handling of zero division.
    assert "Parallel Up" in out
    assert any(term in out for term in ["N/A", "Inf", "nan", "infinity"]), \
        "Expected 'N/A', 'Inf', or 'nan' for Delta EVE (% of T1) when Tier 1 is zero"

    # Check that NII values are still present and correctly formatted
    assert ("-10,000.00" in out or "-10000.00" in out)
    assert ("-25,000.00" in out or "-25000.00" in out)
    assert "Short Rate Down" in out
    assert ("3,000.00" in out or "3000.00" in out)
    assert ("7,500.00" in out or "7500.00" in out)


def test_display_scenario_results_table_partial_scenarios(capture_stdout):
    """
    Test case 4: Verify the function handles cases where not all 6 Basel scenarios are present.
    Only the provided scenarios should be displayed in the table.
    """
    delta_eve_results = {
        "Parallel Up": -500000.0,
        "Flattener": 80000.0,
    }
    delta_nii_results = {
        "Parallel Up": {"1Y": -10000.0, "3Y": -25000.0},
        "Flattener": {"1Y": 1500.0, "3Y": 4000.0},
    }
    tier1_capital = 10_000_000.0

    display_scenario_results_table(delta_eve_results, delta_nii_results, tier1_capital)

    out, err = capture_stdout.readouterr()

    assert err == "", "Stderr should be empty"
    assert "Scenario" in out

    # Check that only the expected scenarios are present
    assert "Parallel Up" in out
    assert "Flattener" in out

    # Verify that the missing scenarios are NOT in the output
    missing_scenarios = [s for s in BASEL_SCENARIOS if s not in delta_eve_results]
    for scenario in missing_scenarios:
        assert scenario not in out, f"Unexpected scenario '{scenario}' found in output."

@pytest.mark.parametrize("eve_input, nii_input, tier1_input, expected_exception", [
    # Test case 5: Verify TypeErrors for invalid input types.
    (None, {}, 100.0, TypeError),  # delta_eve_results is None
    ({}, None, 100.0, TypeError),  # delta_nii_results is None
    ({}, {}, "abc", TypeError),  # tier1_capital is string
    ({}, {}, [100.0], TypeError), # tier1_capital is list
    (123, {}, 100.0, TypeError), # delta_eve_results is int
    ({}, 123, 100.0, TypeError), # delta_nii_results is int
])
def test_display_scenario_results_table_invalid_input_types(eve_input, nii_input, tier1_input, expected_exception):
    """
    Test cases for invalid input types.
    Expects a TypeError when arguments are not of the expected types (dict, dict, float).
    """
    with pytest.raises(expected_exception):
        display_scenario_results_table(eve_input, nii_input, tier1_input)