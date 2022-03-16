"""
Every issue is reported as ``robocop.rules.Message`` object. It can be later printed or used by
post-run reports.

Output message format
---------------------

Output message of rules can be defined with ``-f`` / ``--format`` argument. Default value::

    "{source}:{line}:{col} [{severity}] {rule_id} {desc} ({name})"

.. dropdown:: Available formats:

    * ``source``:     path to the file where the issue occurred
    * ``source_rel``: path to the file where the issue occurred, relative to execution directory
    * ``line``:       line number where the issue starts
    * ``end_line``:   line number where the issue ends
    * ``col``:        column number where the issue starts
    * ``end_col``:    column number where the issue ends
    * ``severity``:   severity of the issue, value of ``robocop.rules.RuleSeverity`` enum
    * ``rule_id``:    rule id (e.g. ``0501``)
    * ``name``:       rule name (e.g. ``line-too-long``)
    * ``desc``:       description of the rule

"""
from enum import Enum
from textwrap import dedent
from functools import total_ordering
from typing import Any, Callable, Union, Pattern, Dict, Optional
from packaging.specifiers import SpecifierSet

from jinja2 import Template

import robocop.exceptions
from robocop.utils import ROBOT_VERSION


@total_ordering
class RuleSeverity(Enum):
    """
    Rule severity.
    It can be configured with ``--configure id_or_msg_name:severity:value``
    where value can be first letter of severity value or whole name, case-insensitive.
    For example ::

        -c line-too-long:severity:e

    will change `line-too-long` rule severity to error.

    You can filter out all rules below given severity value by using following option::

        -t/--threshold <severity value>

    To only report rules with severity W and above::

        --threshold W

    """

    INFO = "I"
    WARNING = "W"
    ERROR = "E"

    @classmethod
    def parser(cls, value: Union[str, "RuleSeverity"]) -> "RuleSeverity":
        # parser can be invoked from Rule() with severity=RuleSeverity.WARNING (enum directly) or
        # from configuration with severity:W (string representation)
        severity = {
            "error": cls.ERROR,
            "e": cls.ERROR,
            "warning": cls.WARNING,
            "w": cls.WARNING,
            "info": cls.INFO,
            "i": cls.INFO,
        }.get(str(value).lower(), None)
        if severity is None:
            raise ValueError(f"Chose one of: {', '.join(sev.value for sev in cls)}") from None
        return severity

    def __str__(self):
        return self.value

    def __lt__(self, other):
        look_up = [sev.value for sev in RuleSeverity]
        return look_up.index(self.value) < look_up.index(other.value)

    def diag_severity(self) -> int:
        return {"I": 3, "W": 2, "E": 1}.get(self.value, 4)


class RuleParam:
    """
    Parameter of the Rule.
    Each rule can have number of parameters (default one is severity).
    """

    def __init__(self, name: str, default: Any, converter: Callable, desc: str):
        """
        :param name: Name of the parameter used when configuring rule (also displayed in the docs)
        :param default: Default value of the parameter
        :param converter: Method used for converting from string. It can be separate method or classmethod from
        particular class (see `:RuleSeverity:` for example of class that is used as rule parameter value).
        It must return value
        :param desc: Description of rule parameter
        """
        self.name = name
        self.converter = converter
        self.desc = desc
        self.raw_value = None
        self._value = None
        self.value = default

    def __str__(self):
        s = f"{self.name} = {self.raw_value}\n" f"        type: {self.converter.__name__}"
        if self.desc:
            s += "\n" f"        info: {self.desc}"
        return s

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self.raw_value = value  # useful for docs/printing
        try:
            self._value = self.converter(value)
        except ValueError as err:
            raise robocop.exceptions.RuleParamFailedInitError(self, value, str(err)) from None


class Rule:
    """
    Robocop linter rule.
    It can be used for reporting issues that are breaking particular rule.
    You can store configuration of the rule inside RuleParam parameters.

    Every rule contains one default RuleParam - severity.
    """

    def __init__(
        self,
        *params: RuleParam,
        rule_id: str,
        name: str,
        msg: str,
        severity: RuleSeverity,
        version: str = None,
        docs: str = "",
    ):
        """
        :param params: RuleParam() instances
        :param rule_id: id of the rule
        :param name: name of the rule
        :param msg: message printed when rule breach is detected
        :param severity: severity of the rule (ie: RuleSeverity.INFO)
        :param version: supported Robot Framework version (ie: >=4.0)
        :param docs: Full documentation of the rule (rst supported)
        description of the rule
        """
        self.rule_id = rule_id
        self.name = name
        self.msg = msg
        self.msg_template = self.get_template(msg)
        self.docs = dedent(docs)
        self.config = {
            "severity": RuleParam(
                "severity", severity, RuleSeverity.parser, "Rule severity (E = Error, W = Warning, I = Info)"
            )
        }
        for param in params:
            self.config[param.name] = param
        self.enabled = True
        self.supported_version = version if version else "All"
        self.enabled_in_version = self.supported_in_rf_version(version)

    @property
    def severity(self):
        return self.config["severity"].value

    @staticmethod
    def supported_in_rf_version(version: str) -> bool:
        if not version:
            return True
        return ROBOT_VERSION in SpecifierSet(version, prereleases=True)

    @staticmethod
    def get_template(msg: str) -> Optional[Template]:
        if "{" in msg:
            return Template(msg)
        return None

    def get_message(self, **kwargs):
        if self.msg_template:
            return self.msg_template.render(**kwargs)
        return self.msg

    def __str__(self):
        return (
            f"Rule - {self.rule_id} [{self.config['severity'].value}]: {self.name}: {self.msg} "
            f"({self.get_enabled_status_desc()})"
        )

    def get_enabled_status_desc(self):
        s = "enabled" if self.enabled else "disabled"
        if not self.enabled and self.supported_version != "All":
            s += f" - supported only for RF version {self.supported_version}"
        return s

    def configure(self, param, value):
        if param not in self.config:
            raise robocop.exceptions.ConfigGeneralError(
                f"Provided param '{param}' for rule '{self.name}' does not exist. "
                f"Available configurable(s) for this rule:\n"
                f"    {self.available_configurables()}"
            )
        self.config[param].value = value

    def available_configurables(self, include_severity: bool = True):
        params = [str(param) for param in self.config.values() if param.name != "severity" or include_severity]
        if not params:
            return ""
        return "\n    ".join(params)

    def prepare_message(self, source, node, lineno, col, end_lineno, end_col, ext_disablers, **kwargs):
        msg = self.get_message(**kwargs)
        return Message(
            rule=self,
            msg=msg,
            source=source,
            node=node,
            lineno=lineno,
            col=col,
            end_col=end_col,
            end_lineno=end_lineno,
            ext_disablers=ext_disablers,
        )

    def matches_pattern(self, pattern: Union[str, Pattern]):
        """check if this rule matches given pattern"""
        if isinstance(pattern, str):
            return pattern in (self.name, self.rule_id)
        return pattern.match(self.name) or pattern.match(self.rule_id)


class Message:
    def __init__(
        self,
        rule: Rule,
        msg,
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
        self.desc = msg
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

    def get_fullname(self) -> str:
        return f"{self.severity.value}{self.rule_id} ({self.name})"

    def to_json(self) -> Dict:
        return {
            "source": self.source,
            "line": self.line,
            "column": self.col,
            "severity": self.severity.value,
            "rule_id": self.rule_id,
            "description": self.desc,
            "rule_name": self.name,
        }
