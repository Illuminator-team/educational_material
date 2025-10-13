import pytest
import shutil
from pathlib import Path
from tests.utils import *


@pytest.mark.usefixtures("tmp_path")
def test_physical_congestion(tmp_path: Path):
    """
    Runs the 'physical_congestion' tutorial notebook and verifies that the generated
    output CSV files match the expected results.

    The notebook is executed in tmp_path. The test then compares selected output files
    against precomputed expected data, checking:
    - File existence
    - Matching shape
    - Identical date columns
    - Numerical equality (within a tolerance) for 'Controller1.dump'
    """
    # Copy entire tutorial directory (including data folder) into tmp_path/tutorial4
    tutorial_dir = Path("tutorials/physical_congestion")
    running_dir = tmp_path / "physical_congestion"
    shutil.copytree(tutorial_dir, running_dir, ignore=ignore_cache_dirs)

    # Run notebook
    execute_notebook(running_dir / "tutorial_physical_congestion.ipynb")

    # Test output files
    output_files = [
        "out_Tutorial_RES.csv",
        "out_Tutorial_RES_Bat.csv",
        "out_Tutorial_bat_elec_assets.csv",
        "out_Tutorial_bat_elec_assets_load_shift.csv"
    ]
    for filename in output_files:
        actual = running_dir / filename
        expected = Path("tests/expected_data/physical_congestion") / filename
        compare_output_files(actual, expected, date_columns=["date"], float_columns=["Controller1.dump"])


@pytest.mark.usefixtures("tmp_path")
def test_power_balance(tmp_path: Path):
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
    # Copy entire tutorial directory (including data folder) into tmp_path/tutorial4
    tutorial_dir = Path("tutorials/power_balance")
    running_dir = tmp_path / "power_balance"
    shutil.copytree(tutorial_dir, running_dir, ignore=ignore_cache_dirs)


    # Run notebook
    execute_notebook(running_dir / "tutorial_power_balance.ipynb")

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
        actual = running_dir / filename
        expected = Path("tests/expected_data/power_balance") / filename
        compare_output_files(actual, expected, date_columns=["date"], float_columns=columns)

