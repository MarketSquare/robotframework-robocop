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
from functools import total_ordering

from packaging.specifiers import SpecifierSet

import robocop.exceptions
from robocop.utils import ROBOT_VERSION


@total_ordering
class RuleSeverity:
    """
    Rule severity.
    It can be configured with ``--configure id_or_msg_name:severity:value``
    where value can be first letter of severity value or whole name, case-insensitive.
    For example ::

        -c line-too-long:severity:e

    will change `line-too-long` rule severity to error.

    You can filter out all rules below given severity value by using following option::

        -t/--threshold <severity value>

    Example::

        --threshold E

    will only report rules with severity E and above.
    """

    look_up = (
        "I",
        "W",
        "E",
    )

    def __init__(self, value):
        severity = {
            "error": "E",
            "e": "E",
            "warning": "W",
            "w": "W",
            "info": "I",
            "i": "I",
        }.get(str(value).lower(), None)
        if severity is None:
            raise ValueError(f"Chose one of: {', '.join(self.look_up)}") from None
        self.value = severity

    def __str__(self):
        return self.value

    def __lt__(self, other):
        return self.look_up.index(self.value) < self.look_up.index(other.value)

    def diag_severity(self):
        return {"I": 3, "W": 2, "E": 1}.get(self.value, 4)

    def full_name(self):
        return {"E": "ERROR", "W": "WARNING", "I": "INFO"}[self.value]


class RuleParam:
    def __init__(self, name, default, converter, desc):
        self.name = name
        self.converter = converter
        self.desc = desc
        self._value = None
        self.value = default

    def __str__(self):
        s = f"{self.name} = {self.value}\n" f"        type: {self.converter.__name__}"
        if self.desc:
            s += "\n" f"        info: {self.desc}"
        return s

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        try:
            self._value = self.converter(value)
        except ValueError as err:
            raise robocop.exceptions.RuleParamFailedInitError(self, value, str(err)) from None


class Rule:
    def __init__(self, *params, rule_id, name, msg, severity, version=None):
        self.rule_id = rule_id
        self.name = name
        self.desc = msg
        self.config = {
            "severity": RuleParam(
                "severity", severity, RuleSeverity, "Rule severity (E = Error, W = Warning, I = Info)"
            )
        }
        for param in params:
            self.config[param.name] = param
        self.enabled = True
        self.enabled_in_version = self.check_robot_version(version)

    @property
    def severity(self):
        return self.config["severity"].value

    @staticmethod
    def check_robot_version(supported_version):
        if not supported_version:
            return True
        return ROBOT_VERSION in SpecifierSet(supported_version)

    def __str__(self):
        return (
            f"Rule - {self.rule_id} [{self.config['severity'].value}]: {self.name}: {self.desc} "
            f'({"enabled" if self.enabled else "disabled"})'
        )

    def configure(self, param, value):
        if param not in self.config:
            raise robocop.exceptions.ConfigGeneralError(
                f"Provided param '{param}' for rule '{self.name}' does not exist. "
                f"Available configurable(s) for this rule:\n"
                f"    {self.available_configurables()}"
            )
        self.config[param].value = value

    def available_configurables(self, include_severity=True):
        params = [str(param) for param in self.config.values() if param.name != "severity" or include_severity]
        if not params:
            return ""
        return "\n    ".join(params)

    def prepare_message(self, *args, source, node, lineno, col, end_lineno, end_col, ext_disablers):
        return Message(
            *args,
            rule=self,
            source=source,
            node=node,
            lineno=lineno,
            col=col,
            end_col=end_col,
            end_lineno=end_lineno,
            ext_disablers=ext_disablers,
        )

    def matches_pattern(self, pattern):
        """check if this rule matches given pattern"""
        if isinstance(pattern, str):
            return pattern in (self.name, self.rule_id)
        return pattern.match(self.name) or pattern.match(self.rule_id)


class Message:
    def __init__(
        self,
        *args,
        rule,
        source,
        node,
        lineno,
        col,
        end_lineno,
        end_col,
        ext_disablers=None,
    ):
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
        self.line = 1
        if node is not None and node.lineno > -1:
            self.line = node.lineno
        if lineno is not None:
            self.line = lineno
        self.col = 1 if col is None else col
        self.end_line = self.line if end_lineno is None else end_lineno
        self.end_col = self.col if end_col is None else end_col
        self.ext_disablers = ext_disablers if ext_disablers else []

    def __lt__(self, other):
        return (self.line, self.col, self.rule_id) < (
            other.line,
            other.col,
            other.rule_id,
        )

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
            "rule_name": self.name,
        }
