from collections import defaultdict
from operator import itemgetter
from robocop.messages import MessageSeverity


def register(linter):
    linter.register_report(RulesByIdReport())
    linter.register_report(RulesBySeverityReport())


class RulesByIdReport:
    def __init__(self):
        self.name = 'rules_by_id'
        self.message_counter = defaultdict(int)

    def add_message(self, message, **kwargs):  # pylint: disable=disable=unused-argument
        self.message_counter[message.get_fullname()] += 1

    def get_report(self):
        message_counter_ordered = sorted([(message, count)
                                          for message, count in self.message_counter.items()],
                                         key=itemgetter(1), reverse=True)
        longest_name = len(max(message_counter_ordered, key=itemgetter(0))[0])
        s = '\nIssues by ids:\n'
        s += '\n'.join(f"{message:{longest_name}} : {count}" for message, count in message_counter_ordered)
        return s


class RulesBySeverityReport:
    def __init__(self):
        self.name = 'rules_by_error_type'
        self.severity_counter = defaultdict(int)

    def add_message(self, message, **kwargs):  # pylint: disable=disable=unused-argument
        self.severity_counter[message.severity] += 1

    def get_report(self):
        issues_count = sum(self.severity_counter.values())
        if not issues_count:
            return 'Found 0 issues'
        s = f'\nFound {issues_count} issues: '
        s += ', '.join(f"{count} {severity.name}(s)" for severity, count in self.severity_counter.items())
        s += '.'
        return s
