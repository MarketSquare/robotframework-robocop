import pytest

from robocop.linter.diagnostics import Diagnostic, Diagnostics
from robocop.linter.reports.rules_by_severity_report import RulesBySeverityReport

FOUR_ISSUES = ["error-message", "warning-message", "info-message", "warning-message"]
PREV_SAME_ISSUES = {"all_issues": 4, "error": 1, "info": 1, "warning": 2}
PREV_EXTRA_ISSUES = {"all_issues": 5, "error": 0, "info": 1, "warning": 2}

EXPECTED_NO_ISSUES = "\nFound 0 issues.\n"
EXPECTED_ONLY_PREV = "\nFound 0 (-4) issues.\n"
EXPECTED_NO_PREV = "\nFound 4 issues: 1 ERROR, 2 WARNINGs, 1 INFO.\n"
EXPECTED_SAME_PREV = "\nFound 4 (+0) issues: 1 (+0) ERROR, 2 (+0) WARNINGs, 1 (+0) INFO.\n"
EXPECTED_EXTRA_PREV = "\nFound 4 (-1) issues: 1 (+1) ERROR, 2 (+0) WARNINGs, 1 (+0) INFO.\n"


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
            (PREV_SAME_ISSUES, False, [], EXPECTED_NO_ISSUES),
            (PREV_SAME_ISSUES, True, [], EXPECTED_ONLY_PREV),
        ],
    )
    def test_rules_by_id_report(
        self,
        previous_results,
        compare_results,
        issues_names,
        expected,
        error_msg,
        warning_msg,
        info_msg,
        config,
        capsys,
    ):
        issues_map = {"error-message": error_msg, "warning-message": warning_msg, "info-message": info_msg}
        config.linter.compare = compare_results
        report = RulesBySeverityReport(config)
        issues = []
        for issue in issues_names:
            issue_def = issues_map[issue]
            msg = Diagnostic(
                rule=issue_def,
                source="some/path/file.robot",
                node=None,
                model=None,
                lineno=50,
                col=10,
                end_lineno=None,
                end_col=None,
            )
            issues.append(msg)
        report.generate_report(prev_results=previous_results, diagnostics=Diagnostics(issues))
        out, _ = capsys.readouterr()
        assert out == expected

    @pytest.mark.parametrize("compare_runs", [True, False])
    def test_persistent_save(self, compare_runs, error_msg, warning_msg, info_msg, config):
        config.linter.compare = compare_runs
        report = RulesBySeverityReport(config)
        issues = []
        for issue in (error_msg, warning_msg, info_msg, info_msg):
            msg = Diagnostic(
                rule=issue,
                source="test.robot",
                node=None,
                model=None,
                lineno=50,
                col=10,
                end_lineno=None,
                end_col=None,
            )
            issues.append(msg)
        expected = {"all_issues": 4, "error": 1, "info": 2, "warning": 1}
        report.generate_report(prev_results={}, diagnostics=Diagnostics(issues))
        results = report.persist_result()
        assert results == expected
