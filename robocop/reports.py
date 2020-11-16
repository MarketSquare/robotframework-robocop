"""
Reports are configurable summaries after lint scan. For example it could be total number of issues discovered.
They are dynamically loaded during setup according to command line configuration.

Each report class collects rules messages from linter and parses it. At the end of the scan it will print the report.

To enable report use ``-r`` / ``--report`` argument and the name of the report.
You can use separate arguments (``-r report1 -r report2``) or comma-separated list (``-r report1,report2``). Example::

    robocop --report rules_by_id,some_other_report path/to/file.robot

To enable all reports use ``--report all``.
"""
from collections import defaultdict
from operator import itemgetter
import robocop.exceptions


class Report:
    def configure(self, name, value, *values):
        raise robocop.exceptions.ConfigGeneralError(
            f"Provided param '{name}' for report '{self.name}' does not exist")  # noqa


class RulesByIdReport(Report):
    """
    Report name: ``rules_by_id``

    Report that groups linter rules messages by rule id and prints it ordered by most common message.
    Example::

        Issues by ids:
        W0502 (too-little-calls-in-keyword) : 5
        W0201 (missing-doc-keyword)         : 4
        E0401 (parsing-error)               : 3
        W0301 (invalid-char-in-name)        : 2
        E0901 (keyword-after-return)        : 1
    """
    def __init__(self):
        self.name = 'rules_by_id'
        self.message_counter = defaultdict(int)

    def add_message(self, message, **kwargs):  # noqa
        self.message_counter[message.get_fullname()] += 1

    def get_report(self):
        message_counter_ordered = sorted([(message, count)
                                          for message, count in self.message_counter.items()],
                                         key=itemgetter(1), reverse=True)
        report = '\nIssues by IDs:\n'
        if not message_counter_ordered:
            report += "No issues found\n"
            return report
        longest_name = max(len(msg[0]) for msg in message_counter_ordered)
        report += '\n'.join(f"{message:{longest_name}} : {count}" for message, count in message_counter_ordered)
        return report


class RulesBySeverityReport(Report):
    """
    Report name: ``rules_by_error_type``

    Report that group linter rules messages by severity and print total of issues per every severity level.

    Example::

        Found 15 issues: 11 WARNING(s), 4 ERROR(s).
    """
    def __init__(self):
        self.name = 'rules_by_error_type'
        self.severity_counter = defaultdict(int)

    def add_message(self, message, **kwargs):  # pylint: disable=unused-argument
        self.severity_counter[message.severity] += 1

    def get_report(self):
        issues_count = sum(self.severity_counter.values())
        if not issues_count:
            return 'Found 0 issues'
        report = f'\nFound {issues_count} issue(s): '
        report += ', '.join(f"{count} {severity.name}(s)" for severity, count in self.severity_counter.items())
        report += '.'
        return report


class ReturnStatusReport(Report):
    """
    Report name: ``return_status``

    Report that checks if number of returned rules messages for given severity value does not exceed preset threshold.
    That information is later used as return status from Robocop.
    """
    def __init__(self):
        self.name = 'return_status'
        self.return_status = 0
        self.counter = RulesBySeverityReport()
        self.quality_gate = {
            'E': 0,
            'W': 100,
            'I': -1
        }

    def configure(self, name, value, *values):
        if name != 'quality_gate':
            super().configure(name, value, *values)
        values = [value] + list(values)
        for val in values:
            try:
                name, count = val.split('=', maxsplit=1)
                if name in self.quality_gate:
                    self.quality_gate[name] = int(count)
            except ValueError:
                continue

    def add_message(self, message, **kwargs):  # pylint: disable=unused-argument
        self.counter.add_message(message, **kwargs)

    def get_report(self):
        for severity, count in self.counter.severity_counter.items():
            threshold = self.quality_gate.get(severity.value, 0)
            if -1 < threshold < count:
                self.return_status = 1
                break
