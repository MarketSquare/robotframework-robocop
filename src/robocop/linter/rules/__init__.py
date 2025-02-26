"""
Robocop rules are internally grouped into checkers. Each checker can scan for multiple related issues
(like ``LengthChecker`` checks both for minimum and maximum length of a keyword). You can refer to
specific rule reported by checkers by its name or id (for example `too-long-keyword` or `0501`).

Checkers are categorized into following categories with a corresponding ID:
    * 01: base
    * 02: documentation
    * 03: naming
    * 04: errors
    * 05: lengths
    * 06: tags
    * 07: comments
    * 08: duplications
    * 09: misc
    * 10: spacing
    * 11-50: not yet used: reserved for future internal checkers
    * 51-99: reserved for external checkers

Checkers have three basic types:

- ``VisitorChecker`` uses Robot Framework parsing API and Python `ast` module for traversing Robot code as nodes,

- ``ProjectChecker`` extends ``VisitorChecker`` and has ``scan_project`` method called after visiting all the files

- ``RawFileChecker`` simply reads Robot file as normal file and scans every line.

Each rule has a unique 4-digit ID that contains:
- a 2-digit category ID (listed above), followed by
- a 2-digit rule number.

Rule ID as well as rule name can be used to refer to the rule (e.g. in include/exclude statements,
configurations etc.). You can optionally configure rule severity or other parameters.
"""

from __future__ import annotations

import ast
import importlib.util
import inspect
from collections import defaultdict
from collections.abc import Generator
from enum import Enum
from functools import total_ordering
from importlib import import_module
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING, Any, Callable, Optional

from jinja2 import Template
from robot.utils import FileReader

from robocop.linter import exceptions
from robocop.linter.exceptions import (
    InvalidExternalCheckerError,
    RuleNotFoundError,
    RuleParamNotFoundError,
    RuleReportsNotFoundError,
)
from robocop.linter.utils import ROBOT_VERSION
from robocop.linter.utils.misc import str2bool
from robocop.linter.utils.version_matching import VersionSpecifier

try:
    from robot.api.parsing import ModelVisitor
except ImportError:
    from robot.parsing.model.visitor import ModelVisitor

if TYPE_CHECKING:
    from re import Pattern

    from robocop.linter.runner import Linter


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
            raise exceptions.InvalidArgumentError(f"Invalid severity value '{value}'. {hint}") from None
        return severity

    def __str__(self):
        return self.value

    def __lt__(self, other):
        look_up = [sev.value for sev in RuleSeverity]
        return look_up.index(self.value) < look_up.index(other.value)

    def diag_severity(self) -> int:
        return {"I": 3, "W": 2, "E": 1}.get(self.value, 4)


def rules_sorted_by_id(rules: dict[str, Rule]) -> list[Rule]:
    """Return rules list from rules dictionary sorted by rule id."""
    return sorted(rules.values(), key=lambda x: int(x.rule_id))


class RuleFilter(str, Enum):
    DEFAULT = "DEFAULT"
    ALL = "ALL"
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
    COMMUNITY = "COMMUNITY"
    DEPRECATED = "DEPRECATED"


def filter_rules_by_pattern(rules: dict[str, Rule], pattern: str) -> list[Rule]:
    """Return sorted list of Rules from rules dictionary, filtered out by pattern."""
    return rules_sorted_by_id(
        {rule.rule_id: rule for rule in rules.values() if rule.matches_pattern(pattern) and not rule.deprecated}
    )


def filter_rules_by_category(rules: dict[str, Rule], category: RuleFilter) -> list[Rule]:
    """Return sorted list of Rules from rules dictionary, filtered by rule category."""
    if category == RuleFilter.DEFAULT:
        rules_by_id = {rule.rule_id: rule for rule in rules.values() if not rule.community_rule and not rule.deprecated}
    elif category == RuleFilter.ALL:
        rules_by_id = {rule.rule_id: rule for rule in rules.values() if not rule.deprecated}
    elif category in (RuleFilter.ENABLED, RuleFilter.DISABLED):
        rules_by_id = {
            rule.rule_id: rule
            for rule in rules.values()
            if category.value.lower() in rule.get_enabled_status_desc()
            and not rule.community_rule
            and not rule.deprecated
        }
    elif category == RuleFilter.COMMUNITY:
        rules_by_id = {rule.rule_id: rule for rule in rules.values() if rule.community_rule and not rule.deprecated}
    elif category == RuleFilter.DEPRECATED:
        rules_by_id = {rule.rule_id: rule for rule in rules.values() if rule.deprecated}
    else:
        raise ValueError(f"Unrecognized rule category '{category}'")
    return rules_sorted_by_id(rules_by_id)


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
            raise exceptions.RuleParamFailedInitError(self, value, str(err)) from None

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
            raise exceptions.InvalidArgumentError(f"Invalid severity value '{value}'. {hint}") from None
        return severity

    def set_thresholds(self, value):
        severity_pairs = value.split(":")
        thresholds = []
        for pair in severity_pairs:
            try:
                sev, param_value = pair.split("=")
            except ValueError:
                raise exceptions.InvalidArgumentError(
                    f"Invalid severity value '{value}'. "
                    f"It should be list of `severity=param_value` pairs, separated by `:`."
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
        version: str | None = None,
        docs: str = "",
        added_in_version: str | None = None,
        enabled: bool = True,
        deprecated: bool = False,
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
            raise exceptions.ConfigGeneralError(
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
        extended_disablers: Optional | None = None,
        sev_threshold_value: Optional | None = None,
        overwrite_severity: Optional | None = None,
    ):
        self.enabled = rule.enabled
        self.rule_id = rule.rule_id
        self.name = rule.name
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


class BaseChecker:
    rules = None

    def __init__(self):
        self.disabled = False
        self.source = None
        self.lines = None
        self.issues = []
        self.rules: dict[str, Rule] = {}
        self.templated_suite = False

    def param(self, rule, param_name):
        try:
            return self.rules[rule].config[param_name].value
        except KeyError:
            if rule not in self.rules:
                raise RuleNotFoundError(rule, self) from None
            if param_name not in self.rules[rule].config:
                raise RuleParamNotFoundError(self.rules[rule], param_name, self) from None
            raise

    def report(
        self,
        rule,
        node=None,
        lineno=None,
        col=None,
        end_lineno=None,
        end_col=None,
        extended_disablers=None,
        sev_threshold_value=None,
        severity=None,
        source: str | None = None,
        **kwargs,
    ):
        rule_def = self.rules.get(rule, None)
        if rule_def is None:
            raise ValueError(f"Missing definition for message with name {rule}")
        rule_threshold = rule_def.config.get("severity_threshold", None)
        if rule_threshold and rule_threshold.substitute_value and rule_threshold.thresholds:
            threshold_trigger = rule_threshold.get_matching_threshold(sev_threshold_value)
            if threshold_trigger is None:
                return
            kwargs[rule_threshold.substitute_value] = threshold_trigger
        message = rule_def.prepare_message(
            source=source or self.source,
            node=node,
            lineno=lineno,
            col=col,
            end_lineno=end_lineno,
            end_col=end_col,
            extended_disablers=extended_disablers,
            sev_threshold_value=sev_threshold_value,
            severity=severity,
            **kwargs,
        )
        if message.enabled:
            self.issues.append(message)


class VisitorChecker(BaseChecker, ModelVisitor):
    def scan_file(self, ast_model, filename, in_memory_content, templated=False) -> list[Message]:
        self.issues: list[Message] = []
        self.source = filename
        self.templated_suite = templated
        if in_memory_content is not None:
            self.lines = in_memory_content.splitlines(keepends=True)
        else:
            self.lines = None
        self.visit_File(ast_model)
        return self.issues

    def visit_File(self, node):  # noqa: N802
        """Perform generic ast visit on file node."""
        self.generic_visit(node)


class ProjectChecker(VisitorChecker):
    def scan_project(self) -> list[Message]:
        """
        Perform checks on the whole project.

        This method is called after visiting all files. Accumulating any necessary data for check depends on
        the checker.
        """
        raise NotImplementedError


class RawFileChecker(BaseChecker):
    def scan_file(self, ast_model, filename, in_memory_content, templated=False) -> list[Message]:
        self.issues: list[Message] = []
        self.source = filename
        self.templated_suite = templated
        if in_memory_content is not None:
            self.lines = in_memory_content.splitlines(keepends=True)
        else:
            self.lines = None
        self.parse_file()
        return self.issues

    def parse_file(self):
        """Read file line by line and for each call check_line method."""
        if self.lines is not None:
            for lineno, line in enumerate(self.lines):
                self.check_line(line, lineno + 1)
        else:
            with FileReader(self.source) as file_reader:
                for lineno, line in enumerate(file_reader.readlines()):
                    self.check_line(line, lineno + 1)

    def check_line(self, line, lineno):
        raise NotImplementedError


def is_checker(checker_class_def: tuple) -> bool:
    return issubclass(checker_class_def[1], BaseChecker) and getattr(checker_class_def[1], "reports", False)


class RobocopImporter:
    def __init__(self, external_rules_paths=None):
        self.internal_checkers_dir = Path(__file__).parent
        self.community_checkers_dir = self.internal_checkers_dir / "community_rules"
        self.external_rules_paths = external_rules_paths
        self.imported_modules = set()
        self.seen_modules = set()
        self.seen_checkers = defaultdict(list)
        self.deprecated_rules = {}

    def get_initialized_checkers(self):
        yield from self._get_checkers_from_modules(self.get_internal_modules(), is_community=False)
        yield from self._get_checkers_from_modules(self.get_community_modules(), is_community=True)
        yield from self._get_checkers_from_modules(self.get_external_modules(), is_community=False)

    def get_internal_modules(self):
        return self.modules_from_paths(list(self.internal_checkers_dir.iterdir()), recursive=False)

    def get_community_modules(self):
        return self.modules_from_paths([self.community_checkers_dir], recursive=True)

    def get_external_modules(self):
        return self.modules_from_paths([*self.external_rules_paths], recursive=True)

    def _get_checkers_from_modules(self, modules, is_community):
        for module in modules:
            if module in self.seen_modules:
                continue
            for _, submodule in inspect.getmembers(module, inspect.ismodule):
                if submodule not in self.seen_modules:
                    yield from self._get_initialized_checkers_from_module(submodule, is_community)
            yield from self._get_initialized_checkers_from_module(module, is_community)

    def _get_initialized_checkers_from_module(self, module, is_community):
        self.seen_modules.add(module)
        for checker_instance in self.get_checkers_from_module(module, is_community):
            if not self.is_checker_already_imported(checker_instance):
                yield checker_instance

    def is_checker_already_imported(self, checker):
        """
        Check if checker was already imported.

        Checker name does not have to be unique, but it should use different rules.
        """
        checker_name = checker.__class__.__name__
        if checker_name in self.seen_checkers and sorted(checker.rules.keys()) in self.seen_checkers[checker_name]:
            return True
        self.seen_checkers[checker_name].append(sorted(checker.rules.keys()))
        return False

    def modules_from_paths(self, paths, recursive=True):
        for path in paths:
            path_object = Path(path)
            if path_object.exists():
                if path_object.is_dir():
                    if not recursive or path_object.name in {".git", "__pycache__"}:
                        continue
                    yield from self.modules_from_paths(list(path_object.iterdir()))
                elif path_object.suffix == ".py":
                    yield self._import_module_from_file(path_object)
            else:
                # if it's not physical path, try to import from installed modules
                try:
                    mod = import_module(path)
                    yield from self._iter_imports(Path(mod.__file__))
                    yield mod
                except ImportError:
                    raise InvalidExternalCheckerError(path) from None

    @staticmethod
    def _import_module_from_file(file_path):
        """
        Import Python file as module.

        importlib does not support importing Python files directly, and we need to create module specification first.
        """
        spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    @staticmethod
    def _find_imported_modules(module: ast.Module):
        """
        Return modules imported using `import module.dot.submodule` syntax.

        `from . import` are ignored - they are later covered by exploring submodules in the same namespace.
        """
        for st in module.body:
            if isinstance(st, ast.Import):
                for n in st.names:
                    yield n.name

    def _iter_imports(self, file_path: Path):
        """Discover Python imports in the file using ast module."""
        try:
            parsed = ast.parse(file_path.read_bytes())
        except:  # noqa: E722
            return
        for import_name in self._find_imported_modules(parsed):
            if import_name not in self.imported_modules:
                self.imported_modules.add(import_name)
            try:
                yield import_module(import_name)
            except ImportError:
                pass

    @staticmethod
    def get_imported_rules(rule_modules):
        for module in rule_modules:
            module_name = module.__name__.split(".")[-1]
            for rule in getattr(module, "rules", {}).values():
                yield module_name, rule

    @staticmethod
    def get_rules_from_module(module) -> dict:
        module_rules = getattr(module, "rules", {})
        if not isinstance(module_rules, dict):
            return {}
        rules = {}
        for rule_id, rule in module_rules.items():
            if rule_id != rule.rule_id:
                raise ValueError(
                    f"Rule id in rules dictionary does not match defined Rule id. {rule_id} != {rule.rule_id}"
                )
            rules[rule.name] = rule
        return rules

    def register_deprecated_rules(self, module_rules: dict[str, Rule]):
        for rule_name, rule_def in module_rules.items():
            if rule_def.deprecated:
                self.deprecated_rules[rule_name] = rule_def
                self.deprecated_rules[rule_def.rule_id] = rule_def

    def get_checkers_from_module(self, module, is_community: bool) -> list:
        classes = inspect.getmembers(module, inspect.isclass)
        checkers = [checker for checker in classes if is_checker(checker)]
        category_id = getattr(module, "RULE_CATEGORY_ID", None)
        module_rules = self.get_rules_from_module(module)
        self.register_deprecated_rules(module_rules)
        checker_instances = []
        for checker in checkers:
            checker_instance = checker[1]()
            valid_checker = True
            for reported_rule in checker_instance.reports:
                if reported_rule not in module_rules:
                    valid_checker = False
                    if module_rules:
                        # empty rules are silently ignored when rules and checkers are imported separately
                        raise RuleReportsNotFoundError(reported_rule, checker_instance) from None
                    continue
                rule = module_rules[reported_rule]
                rule.community_rule = is_community
                rule.category_id = category_id
                checker_instance.rules[reported_rule] = rule
            if valid_checker:
                checker_instances.append(checker_instance)
        return checker_instances


def init(linter: Linter) -> None:
    robocop_importer = RobocopImporter(external_rules_paths=[])  # linter.config.ext_rules FIXME: None is failing
    for checker in robocop_importer.get_initialized_checkers():
        linter.register_checker(checker)
    linter.rules.update(robocop_importer.deprecated_rules)


def get_builtin_rules() -> Generator[tuple[str, Rule], None, None]:
    """Get only rules definitions for documentation generation."""
    robocop_importer = RobocopImporter()
    rule_modules = robocop_importer.get_internal_modules()
    yield from robocop_importer.get_imported_rules(rule_modules)


def get_community_rules() -> Generator[tuple[str, Rule], None, None]:
    """Get only community rules definitions for documentation generation."""
    robocop_importer = RobocopImporter()
    rule_modules = robocop_importer.get_community_modules()
    yield from robocop_importer.get_imported_rules(rule_modules)
