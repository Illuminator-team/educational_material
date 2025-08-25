import pytest
from pathlib import Path
from tests.utils import *


def test_physical_congestion():
    """
    Runs the 'physical_congestion' tutorial notebook and verifies that the generated
    output CSV files match the expected results.

    The notebook is executed in-place. The test then compares selected output files
    against precomputed expected data, checking:
    - File existence
    - Matching shape
    - Identical date columns
    - Numerical equality (within a tolerance) for 'Controller1.dump'
    """
    # Run notebook
    execute_notebook(Path("tutorials/physical_congestion/tutorial_physical_congestion.ipynb"))

    # Test output files
    output_files = [
        "out_Tutorial_RES.csv",
        "out_Tutorial_RES_Bat.csv",
        "out_Tutorial_bat_elec_assets.csv",
        "out_Tutorial_bat_elec_assets_load_shift.csv"
    ]
    for filename in output_files:
        actual = Path("tutorials/physical_congestion") / filename
        expected = Path("tests/expected_data/physical_congestion") / filename
        compare_output_files(actual, expected, ["Controller1.dump"])


def test_power_balance():
    """
    Runs the 'power_balance' tutorial notebook and verifies that the generated
    output CSV files match the expected results.

    The test ensures that all numerical data columns are correct within a small
    tolerance. Specifically, it compares the following columns:
    - Controller1.res_load
    - Controller1.dump
    - PV1.pv_gen
    - Wind1.wind_gen
    - Load1.load_dem

    Checks include:
    - File existence
    - Shape equality
    - Exact match for timestamps
    - Approximate match for float columns
    """
    # Run notebook
    execute_notebook(Path("tutorials/power_balance/tutorial_power_balance.ipynb"))

    # Test output files
    output_files = [
        "out_Tutorial_Power_Balance_a.csv",
        "out_Tutorial_Power_Balance_b.csv"
    ]
    columns = [
        "Controller1.res_load",
        "Controller1.dump",
        "PV1.pv_gen",
        "Wind1.wind_gen",
        "Load1.load_dem"
    ]
    for filename in output_files:
        actual = Path("tutorials/power_balance") / filename
        expected = Path("tests/expected_data/power_balance") / filename
        compare_output_files(actual, expected, columns)

