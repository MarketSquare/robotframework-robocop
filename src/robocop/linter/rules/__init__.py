"""
Robocop rules are internally grouped into checkers. Each checker can scan for multiple related issues
(like ``LengthChecker`` checks both for minimum and maximum length of a keyword). You can refer to
specific rule reported by checkers by its name or id (for example ``too-long-keyword`` or ``LEN01``).

Checkers have three basic types:

- ``VisitorChecker`` uses Robot Framework parsing API and Python `ast` module for traversing Robot code as nodes,

- ``ProjectChecker`` extends ``VisitorChecker`` and has ``scan_project`` method called after visiting all the files

- ``RawFileChecker`` simply reads Robot file as normal file and scans every line.

Each rule has a unique rule id (for example ``DOC01``) consisting of:

- a alphanumeric group name (for example ``DOC``)
- a 2-digit rule number (for example ``01``)

Rule ID as well as rule name can be used to refer to the rule (e.g. in select/ignore statements, configurations etc.).
You can optionally configure rule severity or other parameters.
"""

from __future__ import annotations

import ast
import importlib.util
import inspect
from collections import defaultdict
from enum import Enum
from functools import total_ordering
from importlib import import_module
from inspect import isclass
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING, Any, Callable, NoReturn

from robot.utils import FileReader

from robocop.linter import exceptions
from robocop.linter.diagnostics import Diagnostic
from robocop.linter.exceptions import (
    InvalidExternalCheckerError,
)
from robocop.linter.utils.version_matching import Version, VersionSpecifier

try:
    from robot.api.parsing import ModelVisitor
except ImportError:
    from robot.parsing.model.visitor import ModelVisitor

if TYPE_CHECKING:
    from collections.abc import Generator
    from re import Pattern

    from robot.parsing import File

    from robocop.config import LinterConfig


@total_ordering
class RuleSeverity(Enum):
    """
    It can be configured with::

        robocop check --configure id_or_msg_name.severity=value

    where value can be first letter of severity value or whole name, case-insensitive.

    For example:

    .. tab-set::

        .. tab-item:: Cli

            .. code:: shell

                robocop check -c line-too-long.severity=e

        .. tab-item:: Configuration file

            .. code:: toml

                [robocop.lint]
                configure = [
                    "line-too-long.severity=e"
                ]

    will change `line-too-long` rule severity to error.

    You can filter out all rules below given severity value by using ``-t/--threshold`` option::

        robocop check -t <severity value>

    To only report rules with severity W and above:

    .. tab-set::

        .. tab-item:: Cli

            .. code:: shell

                robocop check --threshold W

        .. tab-item:: Configuration file

            .. code:: toml

                [robocop.lint]
                threshold = "W"

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
    return sorted(rules.values(), key=lambda x: x.rule_id)


class RuleFilter(str, Enum):
    ALL = "ALL"
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
    DEPRECATED = "DEPRECATED"
    STYLE_GUIDE = "STYLE_GUIDE"


def filter_rules_by_pattern(rules: dict[str, Rule], pattern: Pattern) -> list[Rule]:
    """Return sorted list of Rules from rules dictionary, filtered out by pattern."""
    return rules_sorted_by_id(
        {rule.rule_id: rule for rule in rules.values() if rule.matches_pattern(pattern) and not rule.deprecated}
    )


def filter_rules_by_category(rules: dict[str, Rule], category: RuleFilter, target_version: Version) -> list[Rule]:
    """Return sorted list of Rules from rules dictionary, filtered by rule category."""
    if category == RuleFilter.ALL:
        rules_by_id = {rule.rule_id: rule for rule in rules.values() if not rule.deprecated}
    elif category == RuleFilter.ENABLED:
        rules_by_id = {
            rule.rule_id: rule for rule in rules.values() if rule.enabled and not rule.is_disabled(target_version)
        }
    elif category == RuleFilter.DISABLED:
        rules_by_id = {
            rule.rule_id: rule
            for rule in rules.values()
            if not rule.deprecated and (not rule.enabled or rule.is_disabled(target_version))
        }
    elif category == RuleFilter.DEPRECATED:
        rules_by_id = {rule.rule_id: rule for rule in rules.values() if rule.deprecated}
    elif category == RuleFilter.STYLE_GUIDE:
        rules_by_id = {rule.rule_id: rule for rule in rules.values() if not rule.deprecated and rule.style_guide_ref}
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
    def value(self, value) -> None:
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
    def value(self, value) -> None:
        self.set_thresholds(value)

    @staticmethod
    def parse_severity(value):
        # TODO can be replaced with RuleSeverity.parse with False flag
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

    def set_thresholds(self, value) -> None:
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

    def check_condition(self, value: int, threshold: int) -> bool:
        if self.compare_method == "greater":
            return value >= threshold
        if self.compare_method == "less":
            return value <= threshold
        return False

    def get_severity(self, value: int):
        if self.thresholds is None:
            return None
        for severity, threshold in self.thresholds:
            if self.check_condition(value, threshold):
                return severity
        return None

    def get_matching_threshold(self, value: int | None) -> int | None:
        """
        Find first threshold that passes the condition with passed value.

        It's useful to get rule message updated with the threshold value that triggered rule.
        """
        if value is None:
            return None
        for _, threshold in self.thresholds:
            if self.check_condition(value, threshold):
                return threshold
        return None

    def __str__(self):
        return self.name


class Rule:
    """
    Robocop linter rule.

    Class describing Robot Framework code rule, optionally checking the violations and reporting it.

    Attributes:
        name (str): (class attribute) name of the rule
        rule_id (str): (class attribute) id of the rule
        message (str): (class attribute) message of the rule
        severity (RuleSeverity): (class attribute) severity of the rule (ie: RuleSeverity.INFO)
        severity_threshold: (class attribute) Class for dynamically setting rule severity depending on the value
        version (str): (class attribute) supported Robot Framework version (ie: >=4.0)
        added_in_version (str): (class attribute) version of the Robocop when the Rule was created
        enabled (bool): (class attribute) enable/disable rule by default using this parameter
        deprecated (bool): (class attribute) deprecated rule. If rule is used in configuration, it will issue a warning
        file_wide_rule (bool): (class attribute) If set, rule is reported for whole file

    """

    name: str
    rule_id: str
    message: str
    severity: RuleSeverity
    severity_threshold: SeverityThreshold | None = None
    version: str | None = None
    version_spec: VersionSpecifier | None = None
    added_in_version: str | None = None
    enabled: bool = True
    deprecated: bool = False
    file_wide_rule: bool = False
    parameters: list[RuleParam] | None = None
    style_guide_ref: list[str] | None = None

    def __init__(self):
        self.version_spec = VersionSpecifier(self.version) if self.version else None
        self.default_severity = self.severity  # used for defaultConfiguration in Sarif report
        self.config = self._parse_parameters()
        self.supported_version = self.version if self.version else "All"

    def _parse_parameters(self) -> dict[str, RuleParam]:
        """
        Create internal config of the rule.

        By default, each rule contains severity parameter.
        """
        config = {
            "severity": RuleParam(
                name="severity",
                default=self.severity,
                converter=RuleSeverity.parser,
                desc="Rule severity (E = Error, W = Warning, I = Info)",
                show_type="severity",
            ),
        }
        if self.severity_threshold is not None:
            config["severity_threshold"] = self.severity_threshold
        if not self.parameters:
            return config
        for param in self.parameters:
            config[param.name] = param
        return config

    def __getattr__(self, name: str):
        if name in self.config:
            return self.config[name].value
        raise AttributeError(f"Rule {self.name} does not have {name} attribute")

    @property
    def docs(self) -> str:
        return dedent(self.__doc__) if self.__doc__ else ""

    @property
    def description(self) -> str:
        """Description of the rule with rule name, message and documentation."""
        description = f"Rule: [bold]{self.name}[/bold] ({self.rule_id})\n"
        description += f"Message: {self.message}\n"
        description += f"Severity: {self.severity}\n"
        description += self.docs
        return description

    @property
    def description_with_configurables(self):
        description = self.description
        count, configurables = self.available_configurables(include_severity=False)
        if not count:
            return description
        return f"{description}\nConfigurables:\n    {configurables}\n"

    @property
    def deprecation_warning(self) -> str:
        """Used when rule is deprecated and used in configuration."""
        return f"Rule {self.severity}{self.rule_id} {self.name} is deprecated. Remove it from your configuration."

    def get_severity_with_threshold(self, threshold_value):
        if threshold_value is None:
            return self.severity
        if self.severity_threshold is None:
            return self.severity
        severity = self.severity_threshold.get_severity(threshold_value)
        if severity is None:  # TODO
            return self.severity
        return severity

    def supported_in_target_version(self, target_version: Version) -> bool:
        """Validate if rule is enabled for installed Robot Framework or matches configured target version."""
        if not self.version_spec:
            return True
        return target_version in self.version_spec

    def is_disabled(self, target_version: Version) -> bool:
        return self.deprecated or not self.supported_in_target_version(target_version)

    def rule_short_description(self, target_version: Version) -> str:
        if self.deprecated:
            enable_desc = "deprecated"
        elif self.version and not self.supported_in_target_version(target_version):
            enable_desc = f"disabled - supported only for RF version {self.version}"
        elif self.enabled:
            enable_desc = "enabled"
        else:
            enable_desc = "disabled"
        return f"Rule - {self.rule_id} [{self.severity}]: {self.name}: {self.message} ({enable_desc})"

    def __str__(self):
        return f"Rule [{self.rule_id}]: {self.name} {self.message}"

    def configure(self, param: str, value: str) -> None:
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

    def matches_pattern(self, pattern: str | Pattern):  # TODO: move outside, used by one place
        """Check if this rule matches given pattern"""
        if isinstance(pattern, str):
            return pattern in (self.name, self.rule_id)
        return pattern.match(self.name) or pattern.match(self.rule_id)


class BaseChecker:
    rules = None

    def __init__(self):
        self.disabled = False
        self.source = None
        self.lines = None
        self.issues = []
        self.rules: dict[str, Rule] = {}
        self.templated_suite = False

    def report(
        self,
        rule: Rule,
        lineno: int | None = None,
        col: int | None = None,
        end_lineno: int | None = None,
        end_col: int | None = None,
        node=None,
        extended_disablers: tuple[int, int] | None = None,
        sev_threshold_value: int | None = None,
        source: str | None = None,
        **kwargs,
    ) -> None:
        if not rule.enabled:
            return
        # following code is used to dynamically update maximum allowed number if rule has dynamic threshold
        # for example if you set line too long to warn on 120 and fail on 200, it will update the x / 120 to 200
        if rule.severity_threshold and rule.severity_threshold.substitute_value and rule.severity_threshold.thresholds:
            threshold_trigger = rule.severity_threshold.get_matching_threshold(sev_threshold_value)
            if threshold_trigger is None:
                return
            kwargs[rule.severity_threshold.substitute_value] = threshold_trigger
        diagnostic = Diagnostic(
            rule=rule,
            node=node,
            lineno=lineno,
            col=col,
            end_lineno=end_lineno,
            end_col=end_col,
            source=source or self.source,
            extended_disablers=extended_disablers,
            sev_threshold_value=sev_threshold_value,
            **kwargs,
        )
        self.issues.append(diagnostic)


class VisitorChecker(BaseChecker, ModelVisitor):
    def scan_file(
        self, ast_model: File, filename: str, in_memory_content: str | None, templated: bool = False
    ) -> list[Diagnostic]:
        self.issues: list[Diagnostic] = []
        self.source = filename
        self.templated_suite = templated
        if in_memory_content is not None:
            self.lines = in_memory_content.splitlines(keepends=True)
        else:
            self.lines = None
        self.visit_File(ast_model)
        return self.issues

    def visit_File(self, node: File) -> None:  # noqa: N802
        """Perform generic ast visit on file node."""
        self.generic_visit(node)


class ProjectChecker(VisitorChecker):
    def scan_project(self) -> list[Diagnostic]:
        """
        Perform checks on the whole project.

        This method is called after visiting all files. Accumulating any necessary data for check depends on
        the checker.
        """
        raise NotImplementedError


class RawFileChecker(BaseChecker):
    def scan_file(self, ast_model, filename, in_memory_content, templated=False) -> list[Diagnostic]:  # noqa: ARG002
        self.issues: list[Diagnostic] = []
        self.source = filename
        self.templated_suite = templated
        if in_memory_content is not None:
            self.lines = in_memory_content.splitlines(keepends=True)
        else:
            self.lines = None
        self.parse_file()
        return self.issues

    def parse_file(self) -> None:
        """Read file line by line and for each call check_line method."""
        if self.lines is not None:
            for lineno, line in enumerate(self.lines):
                self.check_line(line, lineno + 1)
        else:
            with FileReader(self.source) as file_reader:
                for lineno, line in enumerate(file_reader.readlines()):
                    self.check_line(line, lineno + 1)

    def check_line(self, line, lineno) -> NoReturn:
        raise NotImplementedError


def is_checker(checker_class_def: tuple) -> bool:
    return issubclass(checker_class_def[1], BaseChecker)


def inherits_from(child, parent_name: str) -> bool:
    return parent_name in [c.__name__ for c in inspect.getmro(child)[1:-1]]


def is_rule(rule_class_def: tuple) -> bool:
    return inherits_from(rule_class_def[1], "Rule")
    # return issubclass(rule_class_def[1], Rule) TODO does not work as is_checker for some reason


class RobocopImporter:
    def __init__(self, external_rules_paths=None):
        self.internal_checkers_dir = Path(__file__).parent
        self.external_rules_paths = external_rules_paths
        self.imported_modules = set()
        self.seen_modules = set()
        self.seen_checkers = defaultdict(list)
        self.deprecated_rules = {}

    def get_initialized_checkers(self):
        # TODO: simplify. internal checkers can be static
        yield from self._get_checkers_from_modules(self.get_internal_modules())
        yield from self._get_checkers_from_modules(self.get_external_modules())

    def get_internal_modules(self):
        return self.modules_from_paths(list(self.internal_checkers_dir.iterdir()), recursive=False)

    def get_external_modules(self):
        return self.modules_from_paths([*self.external_rules_paths], recursive=True)

    def _get_checkers_from_modules(self, modules):  # noqa: ANN202
        for module in modules:
            if module in self.seen_modules:
                continue
            for _, submodule in inspect.getmembers(module, inspect.ismodule):
                if submodule not in self.seen_modules:
                    yield from self._get_initialized_checkers_from_module(submodule)
            yield from self._get_initialized_checkers_from_module(module)

    def _get_initialized_checkers_from_module(self, module):  # noqa: ANN202
        self.seen_modules.add(module)
        for checker_instance in self.get_checkers_from_module(module):
            if not self.is_checker_already_imported(checker_instance):
                yield checker_instance

    def is_checker_already_imported(self, checker) -> bool:
        """
        Check if checker was already imported.

        Checker name does not have to be unique, but it should use different rules.
        """
        # FIXME: not needed
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

    def _iter_imports(self, file_path: Path):  # noqa: ANN202
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
            classes = inspect.getmembers(module, inspect.isclass)
            rules = [rule[1]() for rule in classes if is_rule(rule)]
            for rule in rules:
                yield module_name, rule

    def register_deprecated_rules(self, module_rules: dict[str, Rule]) -> None:
        # FIXME: currently deprecated, not used rules are hidden (we could just mentioned them in doc. or create
        # empty checker just for deprecated stuff
        for rule_name, rule_def in module_rules.items():
            if rule_def.deprecated:
                self.deprecated_rules[rule_name] = rule_def
                self.deprecated_rules[rule_def.rule_id] = rule_def

    def _import_rule_class(self, module: ast.Module, rule_class: str) -> Rule | None:
        """
        Import class definition using typing information.

        rule_object: RobocopRule -> imports RobocopRule from current namespace
        rule_object2: other_module.RobocopRule -> imports RobocopRule from other_module namespace
        """
        if "." in rule_class:
            other_module, rule_class = rule_class.rsplit(".", maxsplit=1)
            module = getattr(module, other_module)
        try:
            return getattr(module, rule_class)
        except AttributeError:  # TODO: for example dict[type[Node] typing instead of rule def
            return None

    def get_checker_rules(self, checker_class: type[BaseChecker], module) -> dict[str, Rule]:
        # TODO if other checker uses the same rule, return it instead of creating new instance
        rule_types = getattr(checker_class, "__annotations__", None)
        if rule_types is None:
            return {}
        rules = {}
        for name, rule_class in rule_types.items():
            if isinstance(rule_class, str):  # if from future import annotations was used
                rule_class = self._import_rule_class(module, rule_class)
            if not rule_class or not (isclass(rule_class) and issubclass(rule_class, Rule)):
                continue
            rule_instance = rule_class()
            rules[name] = rule_instance
        return rules

    def get_checkers_from_module(self, module) -> list:
        # FIXME do not inspect / enter external libs such as re..
        classes = inspect.getmembers(module, inspect.isclass)
        checkers = [checker[1]() for checker in classes if is_checker(checker)]
        # self.register_deprecated_rules(module_rules) # FIXME
        checker_instances = []
        for checker in checkers:
            rules = self.get_checker_rules(checker, module)
            if not rules:
                continue
            for attr_name, rule in rules.items():
                checker.rules[rule.name] = rule
                checker.rules[rule.rule_id] = rule
                setattr(checker, attr_name, rule)  # from rule_name: Rule to rule_name = Rule()
            checker_instances.append(checker)
        return checker_instances


def init(config: LinterConfig) -> None:
    robocop_importer = RobocopImporter(external_rules_paths=config.custom_rules)
    for checker in robocop_importer.get_initialized_checkers():
        config.register_checker(checker)
    # linter.rules.update(robocop_importer.deprecated_rules)


def get_builtin_rules() -> Generator[tuple[str, Rule], None, None]:
    """Get only rules definitions for documentation generation."""
    # TODO: refactor
    robocop_importer = RobocopImporter()
    rule_modules = robocop_importer.get_internal_modules()
    yield from robocop_importer.get_imported_rules(rule_modules)


if __name__ == "__main__":
    rules = list(get_builtin_rules())
