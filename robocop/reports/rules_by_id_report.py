from collections import defaultdict
from operator import itemgetter

from robocop.reports import Report
from robocop.rules import Message


class RulesByIdReport(Report):
    """
    Report name: ``rules_by_id``

    Report that groups linter rules messages by rule id and prints it ordered by most common message.
    Example::

        Issues by ID:
        W0502 (too-little-calls-in-keyword) : 5
        W0201 (missing-doc-keyword)         : 4
        E0401 (parsing-error)               : 3
        W0301 (not-allowed-char-in-name)    : 2
        W0901 (keyword-after-return)        : 1
    """

    def __init__(self):
        self.name = "rules_by_id"
        self.description = "Groups detected issues by rule id and prints it ordered by most common"
        self.message_counter = defaultdict(int)

    def add_message(self, message: Message):  # noqa
        self.message_counter[message.get_fullname()] += 1

    def get_report(self) -> str:
        message_counter_ordered = sorted(self.message_counter.items(), key=itemgetter(1), reverse=True)
        report = "\nIssues by ID:\n"
        if not message_counter_ordered:
            report += "No issues found."
            return report
        longest_name = max(len(msg[0]) for msg in message_counter_ordered)
        report += "\n".join(f"{message:{longest_name}} : {count}" for message, count in message_counter_ordered)
        return report
