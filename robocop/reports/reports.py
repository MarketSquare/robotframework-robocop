"""
Each report class collect messages from linter and parse it. At the end of scan it will print
report.

To enable report use ``-r`` / ``--report`` argument and the name of the report.
You can use separate arguments (``-r report1 -r report2``) or comma separated list (``-r report1,report2``). Example::

    robocop --report rules_by_id,some_other_report path/to/file.robot

"""
from collections import defaultdict
from operator import itemgetter


def register(linter):
    linter.register_report(RulesByIdReport())
    linter.register_report(RulesBySeverityReport())


class RulesByIdReport:
    """
    Report name: ``rules_by_id``

    Report that group linter messages by message id and print it ordered by most common message.
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

    def add_message(self, message, **kwargs):  # pylint: disable=disable=unused-argument
        self.message_counter[message.get_fullname()] += 1

    def get_report(self):
        message_counter_ordered = sorted([(message, count)
                                          for message, count in self.message_counter.items()],
                                         key=itemgetter(1), reverse=True)
        report = '\nIssues by ids:\n'
        if not message_counter_ordered:
            report += "No issues found\n"
            return report
        longest_name = len(max(message_counter_ordered, key=itemgetter(0))[0])
        report += '\n'.join(f"{message:{longest_name}} : {count}" for message, count in message_counter_ordered)
        return report


class RulesBySeverityReport:
    """
    Report name: ``rules_by_error_type``

    Report that group linter messages by severity and print total of issues per every severity level.

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
