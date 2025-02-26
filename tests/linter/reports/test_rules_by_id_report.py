import copy

import pytest

from robocop.linter.diagnostics import Diagnostic
from robocop.linter.reports.rules_by_id_report import RulesByIdReport

NO_ISSUES = []
FOUR_ISSUES = ["error-message", "warning-message", "info-message", "warning-message"]
PREV_SAME_ISSUES = {"0102 [W] (warning-message)": 1, "0101 [E] (error-message)": 2, "0103 [I] (info-message)": 1}
PREV_EXTRA_ISSUES = {
    "0102 [W] (warning-message)": 1,
    "0101 [E] (error-message)": 0,
    "0103 [I] (info-message)": 1,
    "0105 [W] (fixed-message)": 1,
    "0104 [W] (fixed-message)": 3,
}

EXPECTED_NO_ISSUES = """
Issues by ID:
No issues found."""
EXPECTED_ONLY_PREV = """
Issues by ID:
0101 [E] (error-message)   : 0 (-2)
0102 [W] (warning-message) : 0 (-1)
0103 [I] (info-message)    : 0 (-1)"""
EXPECTED_NO_PREV = """
Issues by ID:
0102 [W] (warning-message) : 2
0101 [E] (error-message)   : 1
0103 [I] (info-message)    : 1"""
EXPECTED_SAME_PREV = """
Issues by ID:
0102 [W] (warning-message) : 2 (+1)
0101 [E] (error-message)   : 1 (-1)
0103 [I] (info-message)    : 1 (+0)"""
EXPECTED_EXTRA_PREV = """
Issues by ID:
0102 [W] (warning-message) : 2 (+1)
0101 [E] (error-message)   : 1 (+1)
0103 [I] (info-message)    : 1 (+0)
0104 [W] (fixed-message)   : 0 (-3)
0105 [W] (fixed-message)   : 0 (-1)"""


class TestRulesByIdReport:
    @pytest.mark.parametrize(
        ("previous_results", "compare_results", "issues_names", "expected"),
        [
            (None, False, FOUR_ISSUES, EXPECTED_NO_PREV),
            ({}, False, FOUR_ISSUES, EXPECTED_NO_PREV),
            (None, True, FOUR_ISSUES, EXPECTED_NO_PREV),
            ({}, True, FOUR_ISSUES, EXPECTED_NO_PREV),
            (PREV_SAME_ISSUES, False, FOUR_ISSUES, EXPECTED_NO_PREV),
            (PREV_SAME_ISSUES, True, FOUR_ISSUES, EXPECTED_SAME_PREV),
            (PREV_EXTRA_ISSUES, False, FOUR_ISSUES, EXPECTED_NO_PREV),
            (PREV_EXTRA_ISSUES, True, FOUR_ISSUES, EXPECTED_EXTRA_PREV),
            (PREV_SAME_ISSUES, False, NO_ISSUES, EXPECTED_NO_ISSUES),
            (PREV_SAME_ISSUES, True, NO_ISSUES, EXPECTED_ONLY_PREV),
        ],
    )
    def test_rules_by_id_report(
        self, previous_results, compare_results, issues_names, expected, error_msg, warning_msg, info_msg, config
    ):
        issues_map = {"error-message": error_msg, "warning-message": warning_msg, "info-message": info_msg}
        config.linter.compare = compare_results
        report = RulesByIdReport(config)
        for issue in issues_names:
            issue_def = issues_map[issue]
            msg = Diagnostic(
                rule=issue_def,
                source="some/path/file.robot",
                node=None,
                lineno=50,
                col=10,
                end_lineno=None,
                end_col=None,
            )
            report.add_message(msg)
        results_copy = copy.copy(previous_results)  # report pop from dictionary
        assert report.get_report(results_copy) == expected

    @pytest.mark.parametrize("compare_runs", [True, False])
    def test_persistent_save(self, compare_runs, error_msg, warning_msg, info_msg, config):
        config.linter.compare = compare_runs
        report = RulesByIdReport(config)
        for issue in (error_msg, warning_msg, info_msg, info_msg):
            msg = Diagnostic(
                rule=issue,
                source="test.robot",
                node=None,
                lineno=50,
                col=10,
                end_lineno=None,
                end_col=None,
            )
            report.add_message(msg)
        expected = {"0103 [I] (info-message)": 2, "0101 [E] (error-message)": 1, "0102 [W] (warning-message)": 1}
        results = report.persist_result()
        assert results == expected
