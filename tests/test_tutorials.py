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
    # Copy entire tutorial directory (including data folder) into tmp_path/physical_congestion
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
def test_residential(tmp_path: Path):
    """
    Runs the 'residential' tutorial notebook and verifies that the generated
    output CSV files match the expected results.

    The notebook is executed in tmp_path. The test then compares selected output files
    against precomputed expected data, checking:
    - File existence
    - Matching shape
    - Identical date columns
    - Numerical equality (within a tolerance) for some columns (PV derived flows have randomness and are thus omitted)
    """
    # Copy entire tutorial directory (including data folder) into tmp_path/tutorial4
    tutorial_dir = Path("tutorials/residential")
    running_dir = tmp_path / "residential"
    shutil.copytree(tutorial_dir, running_dir, ignore=ignore_cache_dirs)

    # Run notebook
    execute_notebook(running_dir / "Illuminator_BSc_Tutorial.ipynb")

    # Test output files
    output_files = [
        "out_Tutorial4.csv"
    ]
    columns = [
        "Load1.load_dem",
        "CSV_EV_presence.ev1",
        "EV1.demand"
    ]
    for filename in output_files:
        actual = running_dir / filename
        expected = Path("tests/expected_data/residential") / filename
        compare_output_files(actual, expected, date_columns=["date"], float_columns=columns)

@pytest.mark.usefixtures("tmp_path")
def test_markets(tmp_path: Path):
    """
    Test the markets Illuminator scenario by validating multiple output CSV files.

    This test executes the markets scenario and verifies:
    1. Company beta scores.
    2. Main scenario output file.
    3. Operator bid files.
    4. Market result summary files.

    For each check, the test compares actual output CSVs with expected reference 
    CSVs. It ensures file existence, column structure, and correctness of numerical
    and text data.

    Steps:
    ------
    1. Runs the markets scenario via the Illuminator CLI.
    2. Validates beta score CSV.
    3. Validates main output CSV.
    4. Loops over all operator bid CSVs and validates each.
    5. Loops over all market result summary CSVs and validates each.

    Raises:
    -------
    AssertionError:
        - If scenario execution fails.
        - If any output file is missing.
        - If CSV shapes, date columns, text columns, or float columns do not match
          the expected reference.
    """
    # Copy entire configuration directory (including data folder) into tmp_path/markets
    config_dir = Path("tutorials/markets")
    running_dir = tmp_path / "markets"
    shutil.copytree(config_dir, running_dir)

    # Run notebook
    execute_notebook(running_dir / "tutorial_electricity_markets_intro.ipynb")

    # Test output files
    output_files = [
        "out_Tutorial2_company4.csv",
        "out_Tutorial2_conventionalgeneration.csv",
        "out_Tutorial2_RESgeneration.csv",
    ]
    for filename in output_files:
        actual = running_dir / filename
        expected = Path("tests/expected_data/markets") / filename
        compare_output_files(actual, expected, date_columns=["date"], float_columns=["Operator1.market_clearing_price"])

    # Check Bids
    bids = [
        "all_bids_sorted_0.csv"
    ]
    bidcolumns = [
        "Capacity (MW)",
        "Cost (€/MWh)",
        "Availability",
        "Available Capacity (MW)",
        "Bid Capacity (MW)",
        "Bid Price (€/MWh)"
    ]
    for filename in bids:
        actual = running_dir / "results_operator" / filename
        expected = Path("tests/expected_data/markets/") / filename
        compare_output_files(actual, expected, 
            text_columns=["Company", "Technology"], float_columns=bidcolumns)

    # Check Market results
    marketresults = [
        "market_resukts_summary_0.csv"
    ]
    marketcolumns = [
        "Supplied Capacity (MW)",
        "Revenue (€)",
        "Total Costs (€)",
        "Profit (€)"
    ]
    for filename in marketresults:
        actual = running_dir / "results_operator" / filename
        expected = Path("tests/expected_data/markets/") / filename     
        compare_output_files(actual, expected, text_columns=["Company"], float_columns=marketcolumns)   


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
    # Copy entire tutorial directory (including data folder) into tmp_path/power_balance
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

