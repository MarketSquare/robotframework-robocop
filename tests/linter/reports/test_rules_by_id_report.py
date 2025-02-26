import copy

import pytest

from robocop.linter.reports.rules_by_id_report import RulesByIdReport
from robocop.linter.rules import Message

NO_ISSUES = []
FOUR_ISSUES = ["error-message", "warning-message", "info-message", "warning-message"]
PREV_SAME_ISSUES = {"W0102 (warning-message)": 1, "E0101 (error-message)": 2, "I0103 (info-message)": 1}
PREV_EXTRA_ISSUES = {
    "W0102 (warning-message)": 1,
    "E0101 (error-message)": 0,
    "I0103 (info-message)": 1,
    "W0105 (fixed-message)": 1,
    "W0104 (fixed-message)": 3,
}

EXPECTED_NO_ISSUES = """
Issues by ID:
No issues found."""
EXPECTED_ONLY_PREV = """
Issues by ID:
E0101 (error-message)   : 0 (-2)
W0102 (warning-message) : 0 (-1)
I0103 (info-message)    : 0 (-1)"""
EXPECTED_NO_PREV = """
Issues by ID:
W0102 (warning-message) : 2
E0101 (error-message)   : 1
I0103 (info-message)    : 1"""
EXPECTED_SAME_PREV = """
Issues by ID:
W0102 (warning-message) : 2 (+1)
E0101 (error-message)   : 1 (-1)
I0103 (info-message)    : 1 (+0)"""
EXPECTED_EXTRA_PREV = """
Issues by ID:
W0102 (warning-message) : 2 (+1)
E0101 (error-message)   : 1 (+1)
I0103 (info-message)    : 1 (+0)
W0104 (fixed-message)   : 0 (-3)
W0105 (fixed-message)   : 0 (-1)"""


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
        self, previous_results, compare_results, issues_names, expected, error_msg, warning_msg, info_msg
    ):
        issues_map = {"error-message": error_msg, "warning-message": warning_msg, "info-message": info_msg}
        report = RulesByIdReport(compare_results)
        for issue in issues_names:
            issue_def = issues_map[issue]
            msg = Message(
                rule=issue_def,
                msg=issue_def.get_message(),
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
    def test_persistent_save(self, compare_runs, error_msg, warning_msg, info_msg):
        report = RulesByIdReport(compare_runs)
        for issue in (error_msg, warning_msg, info_msg, info_msg):
            msg = Message(
                rule=issue,
                msg=issue.get_message(),
                source="test.robot",
                node=None,
                lineno=50,
                col=10,
                end_lineno=None,
                end_col=None,
            )
            report.add_message(msg)
        expected = {"I0103 (info-message)": 2, "E0101 (error-message)": 1, "W0102 (warning-message)": 1}
        results = report.persist_result()
        assert results == expected
