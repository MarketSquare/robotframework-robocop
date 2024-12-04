"""
Every issue is reported as ``robocop.rules.Message`` object. It can be later printed or used by
post-run reports.

.. _output-message-format:

Output message format
---------------------

Output message of rules can be defined with ``-f`` / ``--format`` argument. Default value::

    "{source}:{line}:{col} [{severity}] {rule_id} {desc} ({name})"

**Available formats**

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

from __future__ import annotations

from enum import Enum
from functools import total_ordering
from textwrap import dedent
from typing import TYPE_CHECKING, Any, Callable, Optional

from jinja2 import Template

import robocop.exceptions
from robocop.utils import ROBOT_VERSION
from robocop.utils.misc import str2bool
from robocop.utils.version_matching import VersionSpecifier
from robocop.version import __version__

if TYPE_CHECKING:
    from re import Pattern


@total_ordering
class RuleSeverity(Enum):
    """
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
    def parser(cls, value: str | RuleSeverity, rule_severity=True) -> RuleSeverity:
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
            severity_values = ", ".join(sev.value for sev in cls)
            hint = f"Choose one from: {severity_values}."
            if rule_severity:
                # it will be reraised as RuleParamFailedInitError
                raise ValueError(hint)
            # invalid severity threshold
            raise robocop.exceptions.InvalidArgumentError(f"Invalid severity value '{value}'. {hint}") from None
        return severity

    def __str__(self):
        return self.value

    def __lt__(self, other):
        look_up = [sev.value for sev in RuleSeverity]
        return look_up.index(self.value) < look_up.index(other.value)

    def diag_severity(self) -> int:
        return {"I": 3, "W": 2, "E": 1}.get(self.value, 4)


class RuleFilter:
    DEFAULT = "DEFAULT"
    ALL = "ALL"
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
    COMMUNITY = "COMMUNITY"
    DEPRECATED = "DEPRECATED"

    def get_filtered_rules(self, rules, pattern):
        if pattern in (self.ENABLED, self.DISABLED):
            rule_by_id = {
                rule.rule_id: rule
                for rule in rules.values()
                if pattern.lower() in rule.get_enabled_status_desc() and not rule.community_rule and not rule.deprecated
            }
        elif pattern == self.COMMUNITY:
            rule_by_id = {rule.rule_id: rule for rule in rules.values() if rule.community_rule and not rule.deprecated}
        elif pattern == self.DEFAULT:
            rule_by_id = {
                rule.rule_id: rule for rule in rules.values() if not rule.community_rule and not rule.deprecated
            }
        elif pattern == self.ALL:
            rule_by_id = {rule.rule_id: rule for rule in rules.values() if not rule.deprecated}
        elif pattern == self.DEPRECATED:
            rule_by_id = {rule.rule_id: rule for rule in rules.values() if rule.deprecated}
        else:
            rule_by_id = {
                rule.rule_id: rule for rule in rules.values() if rule.matches_pattern(pattern) and not rule.deprecated
            }
        return sorted(rule_by_id.values(), key=lambda x: int(x.rule_id))


class RuleParam:
    """
    Parameter of the Rule.
    Each rule can have number of parameters (default one is severity).
    """

    def __init__(self, name: str, default: Any, converter: Callable, desc: str, show_type: str | None = None):
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
        self.show_type = show_type
        self.desc = desc
        self.raw_value = None
        self._value = None
        self.value = default

    def __str__(self):
        s = f"{self.name} = {self.raw_value}\n        type: {self.converter.__name__}"
        if self.desc:
            s += f"\n        info: {self.desc}"
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

    @property
    def param_type(self):
        if self.show_type is None:
            return self.converter.__name__
        return self.show_type


class SeverityThreshold:
    """
    Set issue severity depending on threshold values of configured rule param.

    Rules that support ``SeverityThreshold`` allow you to set thresholds::

        robocop -c line-too-long:severity_threshold:warning=140:error=200

    In this example ``line-too-long`` rule is a warning if the rule param
    ("line_length") exceeds 140, and is an error if it exceeds 200.

    When adding support for ``SeverityThreshold`` to ``Rule``, the value of the param
    needs to be passed to self.report() call as ``sev_threshold_value``.

    ``compare_method`` is used to determine how to compare parameter value
    with threshold ranges.
    """

    def __init__(self, param_name, compare_method="greater", substitute_value=None):
        self.name = "severity_threshold"
        self.param_name = param_name
        self.thresholds = None
        self.compare_method = compare_method
        self.substitute_value = substitute_value

    @property
    def value(self):
        """Property syntax is used to match with RuleParam converting logic."""
        return self.thresholds

    @value.setter
    def value(self, value):
        self.set_thresholds(value)

    @staticmethod
    def parse_severity(value):
        severity = {
            "error": RuleSeverity.ERROR,
            "e": RuleSeverity.ERROR,
            "warning": RuleSeverity.WARNING,
            "w": RuleSeverity.WARNING,
            "info": RuleSeverity.INFO,
            "i": RuleSeverity.INFO,
        }.get(str(value).lower(), None)
        if severity is None:
            severity_values = ", ".join(sev.value for sev in RuleSeverity)
            hint = f"Choose one from: {severity_values}."
            raise robocop.exceptions.InvalidArgumentError(f"Invalid severity value '{value}'. {hint}") from None
        return severity

    def set_thresholds(self, value):
        severity_pairs = value.split(":")
        thresholds = []
        for pair in severity_pairs:
            try:
                sev, param_value = pair.split("=")
            except ValueError:
                raise robocop.exceptions.InvalidArgumentError(
                    f"Invalid severity value '{value}'. It should be list of `severity=param_value` pairs, separated by `:`."
                ) from None
            severity = self.parse_severity(sev)
            thresholds.append((severity, int(param_value)))  # TODO: support non-int params
        self.thresholds = sorted(thresholds, key=lambda x: x[0], reverse=True)

    def check_condition(self, value, threshold):
        if self.compare_method == "greater":
            return value >= threshold
        if self.compare_method == "less":
            return value <= threshold
        return False

    def get_severity(self, value):
        if self.thresholds is None:
            return None
        for severity, threshold in self.thresholds:
            if self.check_condition(value, threshold):
                return severity
        return None

    def get_matching_threshold(self, value):
        """
        Find first threshold that passes the condition with passed value.

        It's useful to get rule message updated with the threshold value that triggered rule.
        """
        if value is None:
            return None
        for _, threshold in self.thresholds:
            if self.check_condition(value, threshold):
                return threshold

    def __str__(self):
        return self.name


class Rule:
    """
    Robocop linter rule.
    It can be used for reporting issues that are breaking particular rule.
    You can store configuration of the rule inside RuleParam parameters.

    Every rule contains one default RuleParam - severity.
    """

    def __init__(
        self,
        *params: RuleParam | SeverityThreshold,
        rule_id: str,
        name: str,
        msg: str,
        severity: RuleSeverity,
        version: str = None,
        docs: str = "",
        added_in_version: str | None = None,
        enabled: bool = True,
        deprecated: bool = False,
        help_url: str | None = None,
    ):
        """
        :param params: RuleParam() or SeverityThreshold() instances
        :param rule_id: id of the rule
        :param name: name of the rule
        :param msg: message printed when rule breach is detected
        :param severity: severity of the rule (ie: RuleSeverity.INFO)
        :param version: supported Robot Framework version (ie: >=4.0)
        :param docs: Full documentation of the rule (rst supported)
        description of the rule
        :param added_in_version: Version of the Robocop when the Rule was created
        :param enabled: Enable/disable rule by default using this parameter
        :param deprecated: Deprecate rule. If rule is used in configuration, it will issue a warning.
        :param help_url: URL to rule documentation or other help resource.
        """
        self.rule_id = rule_id
        self.name = name
        self.msg = msg
        self.msg_template = self.get_template(msg)
        self.default_severity = severity
        self.docs = dedent(docs)
        self.config = {
            "severity": RuleParam(
                name="severity",
                default=severity,
                converter=RuleSeverity.parser,
                desc="Rule severity (E = Error, W = Warning, I = Info)",
                show_type="severity",
            ),
            "enabled": RuleParam(
                name="enabled",
                default=enabled,
                converter=str2bool,
                desc="Rule default enable status",
                show_type="bool",
            ),
        }
        for param in params:
            self.config[param.name] = param
        self.supported_version = version if version else "All"
        self.deprecated = deprecated
        self.enabled_in_version = self.supported_in_rf_version(version)
        self.added_in_version = added_in_version
        self.community_rule = False
        self.category_id = None
        self.help_url = help_url

    @property
    def severity(self):
        return self.config["severity"].value

    @property
    def enabled(self):
        if self.deprecated:
            return False
        return self.config["enabled"].value

    @enabled.setter
    def enabled(self, value):
        self.config["enabled"].value = value

    @property
    def description(self):
        desc = ""
        if not (self.msg.startswith("{{") and self.msg.endswith("}}")):
            desc += f"{self.msg}."
        if self.docs:
            desc += "\n"
            desc += self.docs
        return desc

    @property
    def deprecation_warning(self) -> str:
        """Used when rule is deprecated and used in configuration."""
        return f"Rule {self.severity}{self.rule_id} {self.name} is deprecated. Remove it from your configuration."

    def get_severity_with_threshold(self, threshold_value):
        if threshold_value is None:
            return self.severity
        severity_threshold = self.config.get("severity_threshold", None)
        if severity_threshold is None:
            return self.severity
        severity = severity_threshold.get_severity(threshold_value)
        if severity is None:
            return self.severity
        return severity

    @staticmethod
    def supported_in_rf_version(version: str) -> bool:
        if not version:
            return True
        return all(ROBOT_VERSION in VersionSpecifier(condition) for condition in version.split(";"))

    @staticmethod
    def get_template(msg: str) -> Template | None:
        if "{" in msg:
            return Template(msg)
        return None

    def get_message(self, **kwargs):
        if self.msg_template:
            return self.msg_template.render(**kwargs)
        return self.msg

    def __str__(self):
        return f"Rule - {self.rule_id} [{self.severity}]: {self.name}: {self.msg} ({self.get_enabled_status_desc()})"

    def get_enabled_status_desc(self):
        if self.deprecated:
            return "deprecated"
        if self.enabled:
            return "enabled"
        if self.supported_version != "All":
            return f"disabled - supported only for RF version {self.supported_version}"
        return "disabled"

    def configure(self, param, value):
        if param not in self.config:
            count, configurables_text = self.available_configurables()
            raise robocop.exceptions.ConfigGeneralError(
                f"Provided param '{param}' for rule '{self.name}' does not exist. "
                f"Available configurable{'' if count == 1 else 's'} for this rule:\n"
                f"    {configurables_text}"
            )
        self.config[param].value = value

    def available_configurables(self, include_severity: bool = True):
        params = []
        for param in self.config.values():
            if (param.name == "severity" and not include_severity) or param.name == "enabled":
                continue
            params.append(str(param))
        if not params:
            return 0, ""
        count = len(params)
        text = "\n    ".join(params)
        return count, text

    def prepare_message(
        self,
        source,
        node,
        lineno,
        col,
        end_lineno,
        end_col,
        extended_disablers,
        sev_threshold_value,
        severity,
        **kwargs,
    ):
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
            extended_disablers=extended_disablers,
            sev_threshold_value=sev_threshold_value,
            overwrite_severity=severity,
        )

    def matches_pattern(self, pattern: str | Pattern):
        """Check if this rule matches given pattern"""
        if isinstance(pattern, str):
            return pattern in (self.name, self.rule_id)
        return pattern.match(self.name) or pattern.match(self.rule_id)


class DefaultRule(Rule):
    @property
    def help_url(self) -> str:
        return f"https://robocop.readthedocs.io/en/{__version__}/rules_list.html#{self.name}"

    @help_url.setter
    def help_url(self, _):
        pass


class CommunityRule(Rule):
    @property
    def help_url(self) -> str:
        return f"https://robocop.readthedocs.io/en/{__version__}/community_rules.html#{self.name}"

    @help_url.setter
    def help_url(self, _):
        pass


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
        extended_disablers: Optional = None,
        sev_threshold_value: Optional = None,
        overwrite_severity: Optional = None,
    ):
        self.enabled = rule.enabled
        self.rule_id = rule.rule_id
        self.name = rule.name
        self.help_url = rule.help_url
        self.severity = self.get_severity(overwrite_severity, rule, sev_threshold_value)
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
        self.extended_disablers = extended_disablers if extended_disablers else []

    def __lt__(self, other):
        return (self.line, self.col, self.rule_id) < (
            other.line,
            other.col,
            other.rule_id,
        )

    @staticmethod
    def get_severity(overwrite_severity, rule, sev_threshold_value):
        if overwrite_severity is not None:
            return overwrite_severity
        return rule.get_severity_with_threshold(sev_threshold_value)

    def get_fullname(self) -> str:
        return f"{self.severity.value}{self.rule_id} ({self.name})"

    def to_json(self) -> dict:
        return {
            "source": self.source,
            "line": self.line,
            "end_line": self.end_line,
            "column": self.col,
            "end_column": self.end_col,
            "severity": self.severity.value,
            "rule_id": self.rule_id,
            "description": self.desc,
            "rule_name": self.name,
        }
