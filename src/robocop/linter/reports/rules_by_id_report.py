from collections import defaultdict
from operator import itemgetter

import robocop.linter.reports
from robocop.config import Config
from robocop.linter.diagnostics import Diagnostic


class RulesByIdReport(robocop.linter.reports.ComparableReport):
    """
    **Report name**: ``rules_by_id``

    Report that groups linter rules messages by rule id and prints it ordered by most common message.
    Example::

        Issues by ID:
        VAR03 [W] (variable-overwritten-before-usage) : 5
        DOC01 [W] (missing-doc-keyword)               : 4
        ERR01 [E] (parsing-error)                     : 3
        NAME01 [W] (not-allowed-char-in-name)         : 2
        MISC01 [W] (keyword-after-return)             : 1
    """

    def __init__(self, config: Config):
        self.name = "rules_by_id"
        self.description = "Groups detected issues by rule id and prints it ordered by most common"
        self.message_counter = defaultdict(int)
        super().__init__(config)

    def add_message(self, message: Diagnostic) -> None:
        rule_name = f"{message.rule.rule_id} [{message.severity.value}] ({message.rule.name})"
        self.message_counter[rule_name] += 1

    def persist_result(self) -> dict:
        return dict(self.message_counter.items())

    def get_diff_counter(self, prev_results: dict) -> dict:
        result = {}
        for issue_code, count in self.message_counter.items():
            old_count = prev_results.pop(issue_code, 0)
            result[issue_code] = count - old_count
        for issue_code, old_count in prev_results.items():
            result[issue_code] = -old_count
        return result

    def get_report(self, prev_results) -> str:
        if self.compare_runs and prev_results:
            return self.get_report_with_compare(prev_results)
        return self.get_report_without_compare()

    def get_report_with_compare(self, prev_results: dict) -> str:
        diff_counter = self.get_diff_counter(prev_results)
        message_counter_ordered = sorted(self.message_counter.items(), key=itemgetter(1), reverse=True)
        report = "\nIssues by ID:"
        if message_counter_ordered:
            longest_name = max(len(msg[0]) for msg in message_counter_ordered)
        else:
            longest_name = 0
        fixed_counter_ordered = sorted(diff_counter.items(), key=itemgetter(1))
        if fixed_counter_ordered:
            longest_name = max(longest_name, *(len(msg[0]) for msg in fixed_counter_ordered))
        for message, count in message_counter_ordered:
            diff = "+" if diff_counter[message] >= 0 else ""
            report += f"\n{message:{longest_name}} : {count} ({diff}{diff_counter[message]})"
        for message, count_diff in fixed_counter_ordered:
            if message not in self.message_counter:
                diff = "+" if count_diff >= 0 else ""
                report += f"\n{message:{longest_name}} : 0 ({diff}{count_diff})"
        return report

    def get_report_without_compare(self) -> str:
        message_counter_ordered = sorted(self.message_counter.items(), key=itemgetter(1), reverse=True)
        report = "\nIssues by ID:\n"
        if not message_counter_ordered:
            report += "No issues found."
            return report
        longest_name = max(len(msg[0]) for msg in message_counter_ordered)
        report += "\n".join(f"{message:{longest_name}} : {count}" for message, count in message_counter_ordered)
        return report
