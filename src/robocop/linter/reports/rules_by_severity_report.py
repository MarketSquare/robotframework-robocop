from collections import defaultdict

import robocop.linter.reports
from robocop.config import Config
from robocop.linter.diagnostics import Diagnostics
from robocop.linter.rules import RuleSeverity
from robocop.linter.utils.misc import get_plural_form, get_string_diff


class RulesBySeverityReport(robocop.linter.reports.ComparableReport):
    """
    **Report name**: ``rules_by_error_type``

    Report that groups linter rules messages by severity and prints total of issues per every severity level.

    Example::

        Found 15 issues: 4 ERRORs, 11 WARNINGs.
    """

    def __init__(self, config: Config):
        self.name = "rules_by_error_type"
        self.description = "Prints total number of issues grouped by severity"
        self.severity_counter = defaultdict(int)
        super().__init__(config)

    def persist_result(self) -> dict[str, int]:
        return {
            "all_issues": sum(self.severity_counter.values()),
            "error": self.severity_counter[RuleSeverity.ERROR],
            "warning": self.severity_counter[RuleSeverity.WARNING],
            "info": self.severity_counter[RuleSeverity.INFO],
        }

    def generate_report(self, prev_results: dict, diagnostics: Diagnostics, **kwargs) -> None:  # noqa: ARG002
        for diagnostic in diagnostics:
            self.severity_counter[diagnostic.severity] += 1
        if self.compare_runs and prev_results:
            output = self.get_report_with_compare(prev_results)
        else:
            output = self.get_report_without_compare()
        print(output)

    def get_report_without_compare(self) -> str:
        issues_count = sum(self.severity_counter.values())
        if not issues_count:
            return "\nFound 0 issues."
        report = f"\nFound {issues_count} issue{get_plural_form(issues_count)}: "
        warning_types = []
        for severity, count in self.severity_counter.items():
            warning_types.append(f"{count} {severity.name}{get_plural_form(count)}")
        report += ", ".join(warning_types)
        report += "."
        return report

    def get_report_with_compare(self, prev_results: dict) -> str:
        issues_count = sum(self.severity_counter.values())
        if not issues_count:
            prev_issues = prev_results["all_issues"]
            diff = get_string_diff(prev_issues, issues_count)
            return f"\nFound 0 ({diff}) issues."
        diff = f" ({get_string_diff(prev_results['all_issues'], issues_count)})"
        report = f"\nFound {issues_count}{diff} issue{get_plural_form(issues_count)}: "
        warning_types = []
        for severity, count in self.severity_counter.items():
            diff = f" ({get_string_diff(prev_results[severity.name.lower()], count)})"
            warning_types.append(f"{count}{diff} {severity.name}{get_plural_form(count)}")
        report += ", ".join(warning_types)
        report += "."
        return report
