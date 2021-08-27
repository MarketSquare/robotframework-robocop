"""
Reports are configurable summaries after Robocop scan. For example, it can be a total number of issues discovered.
They are dynamically loaded during setup according to a command line configuration.

Each report class collects rules messages from linter and parses it. At the end of the scan it will print the report.

To enable report use ``-r`` / ``--report`` argument and the name of the report.
You can use separate arguments (``-r report1 -r report2``) or comma-separated list (``-r report1,report2``). Example::

    robocop --report rules_by_id,some_other_report path/to/file.robot

To enable all reports use ``--report all``.
"""
from collections import defaultdict
from timeit import default_timer as timer
from operator import itemgetter
import robocop.exceptions


class Report:
    def configure(self, name, value):
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
        self.description = 'Groups detected issues by rule id and prints it ordered by most common'
        self.message_counter = defaultdict(int)

    def add_message(self, message):  # noqa
        self.message_counter[message.get_fullname()] += 1

    def get_report(self):
        message_counter_ordered = sorted(self.message_counter.items(), key=itemgetter(1), reverse=True)
        report = '\nIssues by IDs:\n'
        if not message_counter_ordered:
            report += "No issues found"
            return report
        longest_name = max(len(msg[0]) for msg in message_counter_ordered)
        report += '\n'.join(f"{message:{longest_name}} : {count}" for message, count in message_counter_ordered)
        return report


class RulesBySeverityReport(Report):
    """
    Report name: ``rules_by_error_type``

    Report that groups linter rules messages by severity and prints total of issues per every severity level.

    Example::

        Found 15 issues: 11 WARNING(s), 4 ERROR(s).
    """
    def __init__(self):
        self.name = 'rules_by_error_type'
        self.description = 'Prints total number of issues grouped by severity'
        self.severity_counter = defaultdict(int)

    def add_message(self, message):
        self.severity_counter[message.severity] += 1

    def get_report(self):
        issues_count = sum(self.severity_counter.values())
        if not issues_count:
            return '\nFound 0 issues'
        report = f'\nFound {issues_count} issue(s): '
        report += ', '.join(f"{count} {severity.name}(s)" for severity, count in self.severity_counter.items())
        report += '.'
        return report


class ReturnStatusReport(Report):
    """
    Report name: ``return_status``

    Report that checks if number of returned rules messages for given severity value does not exceed preset threshold.
    That information is later used as a return status from Robocop.
    """
    def __init__(self):
        self.name = 'return_status'
        self.description = 'Checks if number of specific issues exceed quality gate limits'
        self.return_status = 0
        self.counter = RulesBySeverityReport()
        self.quality_gate = {
            'E': 0,
            'W': 0,
            'I': -1
        }

    def configure(self, name, value):
        if name not in ['quality_gate', 'quality_gates']:
            super().configure(name, value)
        for val in value.split(':'):
            try:
                name, count = val.split('=', maxsplit=1)
                if name.upper() in self.quality_gate:
                    self.quality_gate[name.upper()] = int(count)
            except ValueError:
                continue

    def add_message(self, message):
        self.counter.add_message(message)

    def get_report(self):
        for severity, count in self.counter.severity_counter.items():
            threshold = self.quality_gate.get(severity.value, 0)
            if -1 < threshold < count:
                self.return_status += count - threshold
        self.return_status = min(self.return_status, 255)


class TimeTakenReport(Report):
    """
    Report name: ``scan_timer``

    Report that returns Robocop execution time
    """
    def __init__(self):
        self.name = 'scan_timer'
        self.description = 'Returns Robocop execution time'
        self.start_time = timer()

    def add_message(self, *args):
        pass

    def get_report(self):
        return f'\nScan took {timer() - self.start_time:.3f}s'


class JsonReport(Report):
    """
    Report name: ``json_report``

    Report that returns list of found issues in JSON format.
    """
    def __init__(self):
        self.name = 'json_report'
        self.description = "Accumulates found issues in JSON format"
        self.issues = []

    def add_message(self, message):
        self.issues.append(message.to_json())

    def get_report(self):
        return None


class FileStatsReport(Report):
    """
    Report name: ``file_stats``

    Report that displays overall statistics about number of processed files.
    """
    def __init__(self):
        self.name = 'file_stats'
        self.description = 'Prints overall statistics about number of processed files'
        self.files_count = 0
        self.files_with_issues = set()

    def add_message(self, message):
        self.files_with_issues.add(message.source)

    def get_report(self):
        if not self.files_count:
            return '\nNo files were processed'
        if not self.files_with_issues:
            return f'\nProcessed {self.files_count} file(s) but no issues were found'

        return f'\nProcessed {self.files_count} file(s) from which {len(self.files_with_issues)} ' \
               f'file(s) contained issues'
