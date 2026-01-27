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
import importlib
import importlib.util
import inspect
import pkgutil
import sys
from collections import defaultdict
from enum import Enum
from functools import total_ordering
from importlib import import_module
from inspect import isclass
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING, Any

from typing_extensions import Self

from robocop import __version__, exceptions
from robocop.linter.diagnostics import Diagnostic
from robocop.linter.fix import Fix, FixAvailability
from robocop.parsing.context import Context
from robocop.version_handling import Version, VersionSpecifier

try:
    import annotationlib  # type: ignore[import-not-found]
except ImportError:  # Python < 3.14
    annotationlib = None  # type: ignore[assignment,unused-ignore]

try:
    from robot.api.parsing import ModelVisitor
except ImportError:
    from robot.parsing.model.visitor import ModelVisitor

if TYPE_CHECKING:
    import types
    from collections.abc import Callable, Generator

    from robot.parsing import File
    from robot.parsing.model.statements import Node

    from robocop.config import LinterConfig
    from robocop.config_manager import ConfigManager
    from robocop.linter import sonar_qube
    from robocop.linter.fix import Fix
    from robocop.source_file import SourceFile, VirtualSourceFile


@total_ordering
class RuleSeverity(Enum):
    """
    You can override rule default severity:

        robocop check --configure id_or_msg_name.severity=value

    where value can be first letter of severity value or whole name, case-insensitive.

    For example:

    === ":octicons-command-palette-24: cli"

        ```bash
        robocop check -c line-too-long.severity=e
        ```

    === ":material-file-cog-outline: toml"

        ```toml
        [tool.robocop.lint]
        configure = [
            "line-too-long.severity=e"
        ]
        ```

    will change `line-too-long` rule severity to error.

    You can filter out all rules below given severity value by using ``-t/--threshold`` option:

        robocop check -t <severity value>

    To only report rules with severity W and above:

    === ":octicons-command-palette-24: cli"

        ```bash
        robocop check --threshold W
        ```

    === ":material-file-cog-outline: toml"

        ```toml
        [tool.robocop.lint]
        threshold = "W"
        ```

    """

    INFO = "I"
    WARNING = "W"
    ERROR = "E"

    @classmethod
    def parser(cls, value: str | RuleSeverity, rule_severity: bool = True) -> RuleSeverity:
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
            raise exceptions.ConfigurationError(f"Invalid severity value '{value}'. {hint}") from None
        return severity

    def __str__(self) -> str:
        return self.value

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, RuleSeverity):
            return NotImplemented
        look_up = [sev.value for sev in RuleSeverity]
        return look_up.index(self.value) < look_up.index(other.value)

    def diag_severity(self) -> int:
        return {"I": 3, "W": 2, "E": 1}.get(self.value, 4)


class RuleParam:
    """
    Parameter of the Rule.
    Each rule can have number of parameters (default one is severity).
    """

    def __init__(
        self, name: str, default: Any, converter: Callable[[Any], Any], desc: str, show_type: str | None = None
    ) -> None:
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

    def __str__(self) -> str:
        s = f"{self.name} = {self.raw_value}\n        type: {self.converter.__name__}"
        if self.desc:
            s += f"\n        info: {self.desc}"
        return s

    @property
    def value(self) -> Any:
        return self._value

    @value.setter
    def value(self, value: Any) -> None:
        self.raw_value = value  # useful for docs/printing
        try:
            self._value = self.converter(value)
        except ValueError as err:
            raise exceptions.RuleParamFailedInitError(self, value, str(err)) from None

    @property
    def param_type(self) -> str:
        if self.show_type is None:
            return self.converter.__name__
        return self.show_type


class SeverityThreshold:
    """
    Set issue severity depending on threshold values of configured rule param.

    Rules that support ``SeverityThreshold`` allow you to set thresholds:

        robocop -c line-too-long:severity_threshold:warning=140:error=200

    In this example ``line-too-long`` rule is a warning if the rule param
    ("line_length") exceeds 140, and is an error if it exceeds 200.

    When adding support for ``SeverityThreshold`` to ``Rule``, the value of the param
    needs to be passed to self.report() call as ``sev_threshold_value``.

    ``compare_method`` is used to determine how to compare parameter value
    with threshold ranges.
    """

    def __init__(self, param_name: str, compare_method: str = "greater", substitute_value: str | None = None) -> None:
        self.name = "severity_threshold"
        self.param_name = param_name
        self.thresholds: list[tuple[RuleSeverity, int]] | None = None
        self.compare_method = compare_method
        self.substitute_value = substitute_value

    @property
    def value(self) -> list[tuple[RuleSeverity, int]] | None:
        """Property syntax is used to match with RuleParam converting logic."""
        return self.thresholds

    @value.setter
    def value(self, value: str) -> None:
        self.set_thresholds(value)

    @staticmethod
    def parse_severity(value: str) -> RuleSeverity:
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
            raise exceptions.ConfigurationError(f"Invalid severity value '{value}'. {hint}") from None
        return severity

    def set_thresholds(self, value: str) -> None:
        severity_pairs = value.split(":")
        thresholds = []
        for pair in severity_pairs:
            try:
                sev, param_value = pair.split("=")
            except ValueError:
                raise exceptions.ConfigurationError(
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

    def get_severity(self, value: int) -> RuleSeverity | None:
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
        if value is None or self.thresholds is None:
            return None
        for _, threshold in self.thresholds:
            if self.check_condition(value, threshold):
                return threshold
        return None

    def __str__(self) -> str:
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
        parameters: (class attribute) optional rule parameters
        style_guide_ref (list of str): (class attribute) reference to Robot Framework Style Guide in form of
        '#paragraph' strings
        sonar_qube_attrs: (class attribute) optional SonarQube attributes used for SonarQube report
        deprecated_names: (class attribute) optional tuple of deprecated names for the rule
        fix_suggestion (str): (class attribute) optional suggestion on how to fix the issue
        fix_availability (FixAvailability): The availability of automatic fixes for this rule
        fixable (bool): internal flag to mark whether rule can be fixed

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
    style_guide_ref: list[str] | None = None  # docs only
    sonar_qube_attrs: sonar_qube.SonarQubeAttributes | None = None
    deprecated_names: tuple[str, ...] | None = None  # docs only
    fix_suggestion: str | None = None
    fix_availability: FixAvailability = FixAvailability.NONE
    fixable: bool = False
    checker: BaseChecker  # injected in runtime

    def __init__(self) -> None:
        self.version_spec = VersionSpecifier(self.version) if self.version else None
        self.default_severity = self.severity  # used for defaultConfiguration in Sarif report
        self.config = self._parse_parameters()
        self.supported_version = self.version if self.version else "All"

    def _parse_parameters(self) -> dict[str, RuleParam | SeverityThreshold]:
        """
        Create internal config of the rule.

        By default, each rule contains severity parameter.
        """
        config: dict[str, RuleParam | SeverityThreshold] = {
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

    def __getattr__(self, name: str) -> Any:
        if name in self.config:
            return self.config[name].value
        raise AttributeError(f"Rule {self.name} does not have {name} attribute")

    @property
    def docs(self) -> str:
        return dedent(self.__doc__) if self.__doc__ else ""

    @property
    def docs_url(self) -> str:
        return f"https://robocop.dev/v{__version__}/rules_list/#{self.rule_id.lower()}-{self.name}"

    @property
    def description(self) -> str:
        """Description of the rule with rule name, message and documentation."""
        description = f"Rule: [bold]{self.name}[/bold] ({self.rule_id})\n"
        description += f"Message: {self.message}\n"
        description += f"Severity: {self.severity}\n"
        description += self.docs
        return description

    @property
    def description_with_configurables(self) -> str:
        description = self.description
        count, configurables = self.available_configurables(include_severity=False)
        if not count:
            return description
        return f"{description}\nConfigurables:\n    {configurables}\n"

    @property
    def deprecation_warning(self) -> str:
        """Used when rule is deprecated and used in configuration."""
        return f"Rule {self.severity}{self.rule_id} {self.name} is deprecated. Remove it from your configuration."

    def get_severity_with_threshold(self, threshold_value: int | None) -> RuleSeverity:
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
        if self.fix_availability in (FixAvailability.ALWAYS, FixAvailability.SOMETIMES):
            fix_present = r" \[fixable]"
        else:
            fix_present = ""
        return f"{self.rule_id} [{self.severity}]: {self.name}: {self.message} ({enable_desc}){fix_present}"

    def __str__(self) -> str:
        return f"Rule [{self.rule_id}]: {self.name} {self.message}"

    def configure(self, param: str, value: str) -> None:
        if param not in self.config:
            count, configurables_text = self.available_configurables()
            raise exceptions.ConfigurationError(
                f"Provided param '{param}' for rule '{self.name}' does not exist. "
                f"Available configurable{'' if count == 1 else 's'} for this rule:\n"
                f"    {configurables_text}"
            )
        self.config[param].value = value
        # If you want to use the same parameter name as Rule attribute (for example severity), you need to skip getattr
        if param == "severity":
            self.severity = self.config[param].value

    def available_configurables(self, include_severity: bool = True) -> tuple[int, str]:
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

    def report(
        self,
        lineno: int | None = None,
        col: int | None = None,
        end_lineno: int | None = None,
        end_col: int | None = None,
        node: Node | None = None,
        extended_disablers: tuple[int, int] | None = None,
        sev_threshold_value: int | None = None,
        source: SourceFile | None = None,
        fix: Fix | None = None,
        **kwargs: object,
    ) -> None:
        """Delegate diagnostic message creation to checker class."""
        self.checker.report(
            self,
            lineno=lineno,
            col=col,
            end_lineno=end_lineno,
            end_col=end_col,
            node=node,
            extended_disablers=extended_disablers,
            sev_threshold_value=sev_threshold_value,
            source=source,
            fix=fix,
            **kwargs,
        )

    def fix(self, diag: Diagnostic, source_lines: list[str]) -> Fix | None:  # noqa: ARG002
        """Generate TextEdit to fix the issue or return None if no fix available."""
        return None


class FixableRule(Rule):
    """
    Abstract base class for rules that can automatically fix issues.

    Subclasses must implement the fix() method to provide automatic fixes
    for the issues they detect.
    """

    fix_availability: FixAvailability
    fixable: bool = True

    def fix(self, diag: Diagnostic, source_lines: list[str]) -> Fix | None:
        """
        Generate TextEdit to fix the issue or return None if no fix available.

        Args:
            diag: Diagnostic object containing information about the issue
            source_lines: Source lines from the original file

        Returns:
            Fix object with the corrections, or None if the issue cannot be fixed

        """


class BaseChecker:
    rules: dict[str, Rule] | None = None
    robocop_rule_types: dict[str, Any] | None = None
    context: Context
    source_file: SourceFile

    def __init__(self) -> None:
        self.disabled = False
        self.source: Path = None
        self.lines: list[str] | None = None
        self.issues: list[Diagnostic] = []
        self.rules: dict[str, Rule] = {}
        self.templated_suite = False

    def __new__(cls) -> Self:
        if annotationlib:
            types = annotationlib.get_annotations(cls)  # type: ignore[attr-defined,unused-ignore]
        else:
            types = getattr(cls, "__annotations__", None)
        instance = super().__new__(cls)
        instance.robocop_rule_types = types
        return instance

    def report(
        self,
        rule: Rule,
        lineno: int | None = None,
        col: int | None = None,
        end_lineno: int | None = None,
        end_col: int | None = None,
        node: Node | None = None,
        extended_disablers: tuple[int, int] | None = None,
        sev_threshold_value: int | None = None,
        source: SourceFile | None = None,
        fix: Fix | None = None,
        **kwargs: object,
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
            source=source or self.source_file,
            extended_disablers=extended_disablers,
            sev_threshold_value=sev_threshold_value,
            fix=fix,
            **kwargs,
        )
        self.issues.append(diagnostic)


class VisitorChecker(BaseChecker, ModelVisitor):  # type: ignore[misc]
    def scan_file(self, source_file: SourceFile, templated: bool = False) -> list[Diagnostic]:
        self.issues: list[Diagnostic] = []
        self.source_file = source_file
        self.templated_suite = templated
        self.context = Context()
        self.visit_File(source_file.model)
        return self.issues

    def visit_File(self, node: File) -> None:  # noqa: N802
        """Perform generic ast visit on file node."""
        self.generic_visit(node)


class ProjectChecker(BaseChecker):
    def scan_project(
        self, project_source_file: SourceFile | VirtualSourceFile, config_manager: ConfigManager
    ) -> list[Diagnostic]:
        """
        Perform checks on the whole project.

        This method is called after other checks are finished. Define the main logic of the check here.
        Robocop will access ``self.issues`` list to retrieve list of issues found during the check. Issues are
        reported using ``self.report()`` method.
        """
        raise NotImplementedError


class RawFileChecker(BaseChecker):
    def scan_file(self, source_file: SourceFile, templated: bool = False) -> list[Diagnostic]:
        self.issues: list[Diagnostic] = []
        self.source_file = source_file
        self.templated_suite = templated
        self.parse_file()
        return self.issues

    def parse_file(self) -> None:
        """Read file line by line and for each call check_line method."""
        self.lines = self.source_file.source_lines  # TODO: check if keepends=True was needed
        for lineno, line in enumerate(self.lines):
            self.check_line(line, lineno + 1)

    def check_line(self, line: str, lineno: int) -> None:
        raise NotImplementedError


class AfterRunChecker(BaseChecker):
    def scan_file(self, source_file: SourceFile, **kwargs: object) -> list[Diagnostic]:  # noqa: ARG002
        self.issues: list[Diagnostic] = []
        self.source_file = source_file


def is_checker(checker_class_def: tuple[str, type]) -> bool:
    return issubclass(checker_class_def[1], BaseChecker)


def inherits_from(child: type, parent_name: str) -> bool:
    return parent_name in [c.__name__ for c in inspect.getmro(child)[1:-1]]


def is_rule(rule_class_def: tuple[str, type]) -> bool:
    if rule_class_def[0] in {"Rule", "RuleParam", "RuleSeverity", "FixableRule"}:
        return False
    return inherits_from(rule_class_def[1], "Rule")
    # return issubclass(rule_class_def[1], Rule) TODO does not work as is_checker for some reason


class RobocopImporter:
    def __init__(self, external_rules_paths: list[str] | None = None) -> None:
        self.internal_checkers_dir = Path(__file__).parent
        self.external_rules_paths = external_rules_paths if external_rules_paths else []
        self.imported_modules: set[str] = set()
        self.seen_modules: set[types.ModuleType] = set()
        self.seen_checkers: defaultdict[str, list[list[str]]] = defaultdict(list)
        self.deprecated_rules: dict[str, Rule] = {}

    def get_initialized_checkers(self) -> Generator[BaseChecker, None, None]:
        for module in self.get_internal_modules():
            yield from self._get_initialized_checkers_from_module(module)
        yield from self._get_checkers_from_modules(self.get_external_modules())

    def get_internal_modules(self) -> Generator[types.ModuleType, None, None]:
        rules_package_name = "robocop.linter.rules."
        # when robocop is used as module (in pytest or in IDE tools) we need to clear previously imported rules
        for mod in list(sys.modules.keys()):
            if mod.startswith(rules_package_name):
                del sys.modules[mod]
        for _, module_name, _ in pkgutil.iter_modules([str(self.internal_checkers_dir)]):
            yield importlib.import_module(f"{rules_package_name}{module_name}")

    def get_external_modules(self) -> Generator[types.ModuleType, None, None]:
        for ext_rule_path in self.external_rules_paths:
            # Allow relative imports in external rules folder
            sys.path.append(ext_rule_path)
            sys.path.append(str(Path(ext_rule_path).parent))
            # TODO: we can remove those paths from sys.path after importing
        return self.modules_from_paths([*self.external_rules_paths])

    def _get_checkers_from_modules(
        self, modules: Generator[types.ModuleType, None, None]
    ) -> Generator[BaseChecker, None, None]:
        for module in modules:
            if module in self.seen_modules:
                continue
            for _, submodule in inspect.getmembers(module, inspect.ismodule):
                if submodule not in self.seen_modules:
                    yield from self._get_initialized_checkers_from_module(submodule)
            yield from self._get_initialized_checkers_from_module(module)

    def _get_initialized_checkers_from_module(self, module: types.ModuleType) -> Generator[BaseChecker, None, None]:
        self.seen_modules.add(module)
        for checker_instance in self.get_checkers_from_module(module):
            if not self.is_checker_already_imported(checker_instance):
                yield checker_instance

    def is_checker_already_imported(self, checker: BaseChecker) -> bool:
        """
        Check if checker was already imported.

        Checker name does not have to be unique, but it should use different rules.
        """
        checker_name = checker.__class__.__name__
        if not checker.rules:
            return False
        if checker_name in self.seen_checkers and sorted(checker.rules.keys()) in self.seen_checkers[checker_name]:
            return True
        self.seen_checkers[checker_name].append(sorted(checker.rules.keys()))
        return False

    def modules_from_paths(self, paths: list[str | Path]) -> Generator[types.ModuleType, None, None]:
        for path in paths:
            path_object = Path(path)
            if path_object.exists():
                if path_object.is_dir():
                    if path_object.name in {".git", "__pycache__"}:
                        continue
                    yield from self.modules_from_paths(list(path_object.iterdir()))
                elif path_object.suffix == ".py":
                    yield self._import_module_from_file(path_object)
            else:
                # if it's not physical path, try to import from installed modules
                try:
                    mod = import_module(str(path))
                    if mod.__file__:
                        yield from self._iter_imports(Path(mod.__file__))
                    yield mod
                except ImportError:
                    raise exceptions.InvalidExternalCheckerError(str(path)) from None

    def _import_module_from_file(self, file_path: Path) -> types.ModuleType:
        """
        Import Python file as module.

        importlib does not support importing Python files directly, and we need to create module specification first.
        """
        spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot import module from {file_path}")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        return mod

    @staticmethod
    def _find_imported_modules(module: ast.Module) -> Generator[str, None, None]:
        """
        Return modules imported using `import module.dot.submodule` syntax.

        `from . import` are ignored - they are later covered by exploring submodules in the same namespace.
        """
        for st in module.body:
            if isinstance(st, ast.Import):
                for n in st.names:
                    yield n.name

    def _iter_imports(self, file_path: Path) -> Generator[types.ModuleType, None, None]:
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

    def register_deprecated_rules(self, module_rules: dict[str, Rule]) -> None:
        # FIXME: currently deprecated, not used rules are hidden (we could just mentioned them in doc. or create
        # empty checker just for deprecated stuff
        for rule_name, rule_def in module_rules.items():
            if rule_def.deprecated:
                self.deprecated_rules[rule_name] = rule_def
                self.deprecated_rules[rule_def.rule_id] = rule_def

    def _import_rule_class(self, module: types.ModuleType, rule_class: str) -> type[Rule] | None:
        """
        Import class definition using typing information.

        rule_object: RobocopRule -> imports RobocopRule from current namespace
        rule_object2: other_module.RobocopRule -> imports RobocopRule from other_module namespace
        """
        if "." in rule_class:
            other_module, rule_class = rule_class.rsplit(".", maxsplit=1)
            module = getattr(module, other_module)
        try:
            return getattr(module, rule_class)  # type: ignore[no-any-return]
        except AttributeError:  # TODO: for example dict[type[Node] typing instead of rule def
            return None

    def get_checker_rules(self, checker_class: type[BaseChecker], module: types.ModuleType) -> dict[str, Rule]:
        # TODO if other checker uses the same rule, return it instead of creating new instance
        if not checker_class.robocop_rule_types:
            return {}
        rules: dict[str, Rule] = {}
        for name, rule_class in checker_class.robocop_rule_types.items():
            if isinstance(rule_class, str):  # if from future import annotations was used, or lazy annotation
                rule_class = self._import_rule_class(module, rule_class)
            if not rule_class or not (isclass(rule_class) and issubclass(rule_class, Rule)):
                continue
            rule_instance = rule_class()
            rules[name] = rule_instance
        return rules

    def get_checkers_from_module(self, module: types.ModuleType) -> list[BaseChecker]:
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


class DocumentationImporter(RobocopImporter):
    """Import Robocop internal classes for documentation generation."""

    def get_builtin_rules(self) -> Generator[tuple[str, Rule], None, None]:
        for module in self.get_internal_modules():
            module_name = module.__name__.split(".")[-1]
            classes = inspect.getmembers(module, inspect.isclass)
            rules = [rule[1]() for rule in classes if is_rule(rule)]
            for rule in rules:
                yield module_name, rule
