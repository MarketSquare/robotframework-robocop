"""
Every issue is reported as ``robocop.rules.Message`` object. It can be later printed or used by
post-run reports.

Output message format
---------------------

Output message of rules can be defined with ``-f`` / ``--format`` argument. Default value::

    "{source}:{line}:{col} [{severity}] {rule_id} {desc} ({name})"

Available formats:
  * ``source``:     path to the file where the issue occurred
  * ``source_rel``: path to the file where the issue occurred, relative to execution directory
  * ``line``:       line number where the issue starts
  * ``end_line``:   line number where the issue ends
  * ``col``:        column number where the issue starts
  * ``end_col``:    column number where the issue ends
  * ``severity``:   severity of the issue, value of ``robocop.rules.RuleSeverity`` enum
  * ``rule_id``:    rule id (e.g. 0501)
  * ``name``:       rule name (e.g. ``line-too-long`)
  * ``desc``:       description of the rule
"""
from enum import Enum
from functools import total_ordering
import robocop.exceptions


@total_ordering
class RuleSeverity(Enum):
    """
    Rule severity.
    It can be configured with ``--configure id_or_msg_name:severity:value``
    where value can be first letter of severity value or whole name, case insensitive.
    For example ::

        -c line-too-long:severity:e

    will change `line-too-long` rule severity to error.

    You can filter out all rules below given severity value by using following option::

        -t/--threshold <severity value>

    Example::

        --threshold E

    will only report rules with severity E and above.
    """
    INFO = "I"
    WARNING = "W"
    ERROR = "E"

    def __lt__(self, other):
        look_up = [sev.value for sev in RuleSeverity]
        return look_up.index(self.value) < look_up.index(other.value)


class Rule:
    def __init__(self, rule_id, body):
        self.rule_id = rule_id
        self.name = ''
        self.desc = ''
        self.source = None
        self.enabled = True
        self.severity = RuleSeverity.INFO
        self.configurable = []
        self.parse_body(body)

    def __str__(self):
        return f'Rule - {self.rule_id} [{self.severity.value}]: {self.name}: {self.desc} ' \
               f'({"enabled" if self.enabled else "disabled"})'

    def change_severity(self, value):
        severity = {
            'error': 'E',
            'e': 'E',
            'warning': 'W',
            'w': 'W',
            'info': 'I',
            'i': 'I'
        }.get(str(value).lower(), None)
        if severity is None:
            raise robocop.exceptions.InvalidRuleSeverityError(self.name, value)
        self.severity = RuleSeverity(severity)

    def get_configurable(self, param):
        for configurable in self.configurable:
            if configurable[0] == param:
                return configurable
        return None

    @staticmethod
    def get_configurable_desc(conf, default=None):
        desc = f'{conf[0]} = {default}\n' \
            f'        type: {conf[2].__name__}'
        if len(conf) == 4:
            desc += '\n' \
                 f'        info: {conf[3]}'
        return desc

    @staticmethod
    def get_default_value(param, checker):
        return None if checker is None else checker.__dict__.get(param, None)

    def available_configurables(self, include_severity=True, checker=None):
        configurables = ['severity'] if include_severity else []
        for conf in self.configurable:
            default = self.get_default_value(conf[1], checker)
            configurables.append(self.get_configurable_desc(conf, default))
        if not configurables:
            return ''
        return '\n    '.join(configurables)

    def parse_body(self, body):
        if isinstance(body, tuple) and len(body) >= 3:
            self.name, self.desc, self.severity, *self.configurable = body
        else:
            raise robocop.exceptions.InvalidRuleBodyError(self.rule_id, body)
        for configurable in self.configurable:
            if not isinstance(configurable, tuple) or len(configurable) not in (3, 4):
                raise robocop.exceptions.InvalidRuleConfigurableError(self.rule_id, body)

    def prepare_message(self, *args, source, node, lineno, col, end_lineno, end_col):
        return Message(
            *args,
            rule=self,
            source=source,
            node=node,
            lineno=lineno,
            col=col,
            end_col=end_col,
            end_lineno=end_lineno
        )

    def matches_pattern(self, pattern):
        """ check if this rule matches given pattern """
        if isinstance(pattern, str):
            return pattern in (self.name, self.rule_id)
        return pattern.match(self.name) or pattern.match(self.rule_id)


class Message:
    def __init__(self, *args, rule, source, node, lineno, col, end_lineno, end_col):
        self.enabled = rule.enabled
        self.rule_id = rule.rule_id
        self.name = rule.name
        self.severity = rule.severity
        self.desc = rule.desc
        try:
            self.desc %= args
        except TypeError as err:
            raise robocop.exceptions.InvalidRuleUsageError(rule.rule_id, err)
        self.source = source
        self.line = 0
        if node is not None and node.lineno > -1:
            self.line = node.lineno
        if lineno is not None:
            self.line = lineno
        self.col = 0 if col is None else col
        self.end_line = self.line if end_lineno is None else end_lineno
        self.end_col = self.col if end_col is None else end_col

    def __lt__(self, other):
        return (self.line, self.col, self.rule_id) < (other.line, other.col, other.rule_id)

    def get_fullname(self):
        return f"{self.severity.value}{self.rule_id} ({self.name})"

    def to_json(self):
        return {
                "source": self.source,
                "line": self.line,
                "column": self.col,
                "severity": self.severity.value,
                "rule_id": self.rule_id,
                "description": self.desc,
                "rule_name": self.name
            }
