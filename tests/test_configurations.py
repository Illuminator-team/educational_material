# import pytest
# import shutil
# from pathlib import Path
# from tests.utils import *

# # TODO add test for IDE case if we end up adding IDE case here
# @pytest.mark.usefixtures("tmp_path")
# def test_IDEcase(tmp_path: Path):
#     """
#     Test the IDE_case Illuminator scenario by validating multiple output CSV files.

#     This test executes the IDE_case scenario and verifies:
#     1. Company beta scores.
#     2. Main scenario output file.
#     3. Operator bid files.
#     4. Market result summary files.

#     For each check, the test compares actual output CSVs with expected reference 
#     CSVs. It ensures file existence, column structure, and correctness of numerical
#     and text data.

#     Steps:
#     ------
#     1. Runs the IDE_case scenario via the Illuminator CLI.
#     2. Validates beta score CSV.
#     3. Validates main output CSV.
#     4. Loops over all operator bid CSVs and validates each.
#     5. Loops over all market result summary CSVs and validates each.

#     Raises:
#     -------
#     AssertionError:
#         - If scenario execution fails.
#         - If any output file is missing.
#         - If CSV shapes, date columns, text columns, or float columns do not match
#           the expected reference.
#     """
#     # Copy entire configuration directory (including data folder) into tmp_path/IDE_case
#     config_dir = Path("configurations/IDE_case")
#     running_dir = tmp_path / "IDE_case"
#     shutil.copytree(config_dir, running_dir)

#     # Run scenario
#     execute_scenario(running_dir / "Tutorial_2_ide_test.yaml")

#     # Check Company betascores
#     actual = running_dir / "justice_agent_results/betascores_4.csv"
#     expected = Path("tests/expected_data/IDE_case/betascores_4.csv")
#     compare_output_files(actual, expected, float_columns=["Company1", "Company2", "Company3"])

#     # Check out file
#     actual = running_dir / "out_ide_case_test.csv"
#     expected = Path("tests/expected_data/IDE_case/out_ide_case_test.csv")
#     compare_output_files(actual, expected, date_columns=["date"],
#        float_columns=["Operator1.market_clearing_price", "Operator1.demand", "JusticeAgent1.justice_score"])

#     # Check Bids
#     bids = [
#         "all_bids_sorted_0.csv",
#         "all_bids_sorted_1.csv",
#         "all_bids_sorted_2.csv",
#         "all_bids_sorted_3.csv",
#         "all_bids_sorted_4.csv"
#     ]
#     bidcolumns = [
#         "Capacity (MW)",
#         "Cost (€/MWh)",
#         "Availability",
#         "Available Capacity (MW)",
#         "Bid Capacity (MW)",
#         "Bid Price (€/MWh)"
#     ]
#     for filename in bids:
#         actual = running_dir / "operator_results/" / filename
#         expected = Path("tests/expected_data/IDE_case/") / filename
#         compare_output_files(actual, expected, 
#             text_columns=["Company", "Technology"], float_columns=bidcolumns)

#     # Check Market results
#     marketresults = [
#         "market_resukts_summary_0.csv",
#         "market_resukts_summary_1.csv",
#         "market_resukts_summary_2.csv",
#         "market_resukts_summary_3.csv",
#         "market_resukts_summary_4.csv"
#     ]
#     marketcolumns = [
#         "Supplied Capacity (MW)",
#         "Revenue (€)",
#         "Total Costs (€)",
#         "Profit (€)"
#     ]
#     for filename in marketresults:
#         actual = running_dir / "operator_results/" / filename
#         expected = Path("tests/expected_data/IDE_case/") / filename     
#         compare_output_files(actual, expected, text_columns=["Company"], float_columns=marketcolumns)   
