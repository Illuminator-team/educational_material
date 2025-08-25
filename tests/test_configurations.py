import pytest
from pathlib import Path
from tests.utils import *


def test_tutorial4():
    """
    Test the Tutorial4 Illuminator scenario by verifying its output CSV file.

    This test executes the scenario defined in the Tutorial4 YAML configuration 
    and compares the generated output file with an expected reference file. It 
    checks that the output file exists, has the same structure as expected, and 
    that key numerical columns match within a tolerance.

    Steps:
    ------
    1. Runs the scenario using the Illuminator CLI.
    2. Loads the actual and expected output CSVs.
    3. Compares a predefined list of numeric columns for accuracy.

    Raises:
    -------
    AssertionError:
        - If scenario execution fails.
        - If the output file is missing.
        - If file shapes or date columns do not match.
        - If float column values differ beyond allowed tolerance.
    """
    # Run scenario
    execute_scenario(Path("configurations/tutorial4/Tutorial4.yaml"))

    # Check output file
    actual = Path("configurations/tutorial4/out_Tutorial4.csv")
    expected = Path("tests/expected_data/tutorial4/out_Tutorial4.csv")
    columns = [
        "PV1.pv_gen",
        "Load1.load_dem",
        "CSV_EV_presence.ev1",
        "EV1.demand",
        "Battery1.soc",
        "Battery1.p_out",
        "Controller1.flow2b",
        "Controller1.res_load",
        "Controller1.dump"
    ]
    compare_output_files(actual, expected, date_columns=["date"], float_columns=columns)


def test_IDEcase():
    """
    Test the IDE_case Illuminator scenario by validating multiple output CSV files.

    This test executes the IDE_case scenario and verifies:
    1. Company beta scores.
    2. Main scenario output file.
    3. Operator bid files.
    4. Market result summary files.

    For each check, the test compares actual output CSVs with expected reference 
    CSVs. It ensures file existence, column structure, and correctness of numerical
    and text data.

    Steps:
    ------
    1. Runs the IDE_case scenario via the Illuminator CLI.
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
    # Run scenario
    execute_scenario(Path("configurations/IDE_case/Tutorial_2_ide_test.yaml"))

    # Check Company betascores
    actual = Path("configurations/IDE_case/justice_agent_results/betascores_4.csv")
    expected = Path("tests/expected_data/IDE_case/betascores_4.csv")
    compare_output_files(actual, expected, float_columns=["Company1", "Company2", "Company3"])

    # Check out file
    actual = Path("configurations/IDE_case/out_ide_case_test.csv")
    expected = Path("tests/expected_data/IDE_case/out_ide_case_test.csv")
    compare_output_files(actual, expected, date_columns=["date"],
       float_columns=["Operator1.market_clearing_price", "Operator1.demand", "JusticeAgent1.justice_score"])

    # Check Bids
    bids = [
        "all_bids_sorted_0.csv",
        "all_bids_sorted_1.csv",
        "all_bids_sorted_2.csv",
        "all_bids_sorted_3.csv",
        "all_bids_sorted_4.csv"
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
        actual = Path("configurations/IDE_case/operator_results/") / filename
        expected = Path("tests/expected_data/IDE_case/") / filename
        compare_output_files(actual, expected, 
            text_columns=["Company", "Technology"], float_columns=bidcolumns)

    # Check Market results
    marketresults = [
        "market_resukts_summary_0.csv",
        "market_resukts_summary_1.csv",
        "market_resukts_summary_2.csv",
        "market_resukts_summary_3.csv",
        "market_resukts_summary_4.csv"
    ]
    marketcolumns = [
        "Supplied Capacity (MW)",
        "Revenue (€)",
        "Total Costs (€)",
        "Profit (€)"
    ]
    for filename in marketresults:
        actual = Path("configurations/IDE_case/operator_results/") / filename
        expected = Path("tests/expected_data/IDE_case/") / filename     
        compare_output_files(actual, expected, text_columns=["Company"], float_columns=marketcolumns)   
