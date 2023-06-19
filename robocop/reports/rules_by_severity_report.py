from collections import defaultdict

from robocop.reports import Report
from robocop.rules import Message


class RulesBySeverityReport(Report):
    """
    Report name: ``rules_by_error_type``

    Report that groups linter rules messages by severity and prints total of issues per every severity level.

    Example::

        Found 15 issues: 4 ERRORs, 11 WARNINGs.
    """

    def __init__(self):
        self.name = "rules_by_error_type"
        self.description = "Prints total number of issues grouped by severity"
        self.severity_counter = defaultdict(int)

    def add_message(self, message: Message):
        self.severity_counter[message.severity] += 1

    def get_report(self) -> str:
        issues_count = sum(self.severity_counter.values())
        if not issues_count:
            return "\nFound 0 issues."

        report = "\nFound 1 issue: " if issues_count == 1 else f"\nFound {issues_count} issues: "
        warning_types = []
        for severity, count in self.severity_counter.items():
            plural = "" if count == 1 else "s"
            warning_types.append(f"{count} {severity.name}{plural}")
        report += ", ".join(warning_types)
        report += "."
        return report
