from __future__ import annotations

import ast
import importlib
import importlib.util
import inspect
import pkgutil
import sys
from collections import defaultdict
from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING

import click

try:
    from robot.api import Languages  # RF 6.0
except ImportError:
    Languages = None

from robocop import exceptions
from robocop.config.parser import compile_rule_pattern
from robocop.formatter.formatters import FORMATTERS, import_formatter
from robocop.linter.rules import AfterRunChecker, BaseChecker, ProjectChecker, Rule, RuleSeverity, VisitorChecker
from robocop.runtime.resolved_config import ResolvedConfig
from robocop.version_handling import ROBOT_VERSION, Version

if TYPE_CHECKING:
    import types
    from collections.abc import Generator

    from robocop.config.schema import Config, SkipConfig, WhitespaceConfig
    from robocop.formatter.formatters import Formatter


class RuleMatcher:
    def __init__(
        self,
        select: list[str],
        extend_select: list[str],
        ignore: list[str],
        target_version: Version,
        threshold: RuleSeverity,
        fixable: list[str],
        unfixable: list[str],
    ) -> None:
        self.include_rules = {rule for rule in select if "*" not in rule}
        self.include_rules_patterns = {compile_rule_pattern(rule) for rule in select if "*" in rule}
        self.extend_include_rules = {rule for rule in extend_select if "*" not in rule}
        self.extend_include_rules_patterns = {compile_rule_pattern(rule) for rule in extend_select if "*" in rule}
        self.exclude_rules = {rule for rule in ignore if "*" not in rule}
        self.exclude_rules_patterns = {compile_rule_pattern(rule) for rule in ignore if "*" in rule}
        self.target_version = target_version
        self.threshold = threshold
        self.fixable = fixable
        self.unfixable = unfixable

    def is_rule_enabled(self, rule: Rule) -> bool:  # noqa: PLR0911
        if self.is_rule_disabled(rule):
            return False
        if "ALL" in self.include_rules:
            return True
        if self.extend_include_rules or self.extend_include_rules_patterns:
            if rule.rule_id in self.extend_include_rules or rule.name in self.extend_include_rules:
                return True
            if any(
                pattern.match(rule.rule_id) or pattern.match(rule.name)
                for pattern in self.extend_include_rules_patterns
            ):
                return True
        if self.include_rules or self.include_rules_patterns:  # if any include pattern, it must match with something
            if rule.rule_id in self.include_rules or rule.name in self.include_rules:
                return True
            return any(
                pattern.match(rule.rule_id) or pattern.match(rule.name) for pattern in self.include_rules_patterns
            )
        return rule.enabled

    def is_rule_disabled(self, rule: Rule) -> bool:
        if rule.is_disabled(self.target_version):
            return True
        if rule.severity < self.threshold and not rule.config.get("severity_threshold"):
            return True
        if rule.rule_id in self.exclude_rules or rule.name in self.exclude_rules:
            return True
        return any(pattern.match(rule.rule_id) or pattern.match(rule.name) for pattern in self.exclude_rules_patterns)

    def is_rule_fixable(self, rule: Rule) -> bool:
        """
        Determine if rule is fixable.

        Rule is fixable if it implements FixableRule class and its rule id or name matches
        with --fixable and --unfixable options.
        """
        if not rule.fixable:
            return False
        if rule.rule_id in self.unfixable or rule.name in self.unfixable:
            return False
        if self.fixable:
            return rule.rule_id in self.fixable or rule.name in self.fixable
        return True


def is_checker(checker_class_def: tuple[str, type]) -> bool:
    return issubclass(checker_class_def[1], BaseChecker)


def inherits_from(child: type, parent_name: str) -> bool:
    return parent_name in [c.__name__ for c in inspect.getmro(child)[1:-1]]


def is_rule(rule_class_def: tuple[str, type]) -> bool:
    if rule_class_def[0] in {"Rule", "RuleParam", "RuleSeverity", "FixableRule"}:
        return False
    return inherits_from(rule_class_def[1], "Rule")
    # return issubclass(rule_class_def[1], Rule) TODO does not work as is_checker for some reason


def can_run_in_robot_version(formatter: Formatter, overwritten: bool, target_version: int) -> bool:
    min_version = getattr(formatter, "MIN_VERSION", None)
    if not min_version or target_version >= min_version:
        return True
    if overwritten:
        # --select FormatterDisabledInVersion or --configure FormatterDisabledInVersion.enabled=True
        if target_version == ROBOT_VERSION.major:
            click.echo(
                f"{formatter.__class__.__name__} formatter requires Robot Framework {min_version}.* "
                f"version but you have {ROBOT_VERSION} installed. "
                f"Upgrade installed Robot Framework if you want to use this formatter.",
                err=True,
            )
        else:
            click.echo(
                f"{formatter.__class__.__name__} formatter requires Robot Framework {min_version}.* "
                f"version but you set --target-version rf{target_version}. "
                f"Set --target-version to {min_version} or do not forcefully enable this formatter "
                f"with --select / enable parameter.",
                err=True,
            )
    return False


class LinterImporter:
    def __init__(self, external_rules_paths: list[str] | None = None) -> None:
        self.internal_checkers_dir = Path(__file__).parent.parent / "linter" / "rules"
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
            if not rule_class or not (inspect.isclass(rule_class) and issubclass(rule_class, Rule)):
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


class DocumentationImporter(LinterImporter):
    """Import Robocop internal classes for documentation generation."""

    def get_builtin_rules(self) -> Generator[tuple[str, Rule], None, None]:
        for module in self.get_internal_modules():
            module_name = module.__name__.split(".")[-1]
            classes = inspect.getmembers(module, inspect.isclass)
            rules = [rule[1]() for rule in classes if is_rule(rule)]
            for rule in rules:
                yield module_name, rule


def map_configure(configure: list[str]) -> dict[str, dict[str, str]]:
    """
    Aggregate configure for rule, reports or formatters and their parameters.

    For example:

        robocop format -c MyFormatter.param=value -c MyFormatter2.param=value -c MyFormatter.param=value

    will return:

        {"MyFormatter": {"param": "value", "param2": "value"}, "MyFormatter2": {"param": "value"}}

    """
    configurables: dict[str, dict[str, str]] = {}
    for config in configure:
        try:
            name, param_and_value = config.split(".", maxsplit=1)
            param, value = param_and_value.split("=", maxsplit=1)
            name, param, value = name.strip(), param.strip(), value.strip()
        except ValueError:
            raise exceptions.InvalidConfigurationFormatError(config) from None
        else:
            if name not in configurables:
                configurables[name] = {}
            configurables[name][param] = value
    return configurables


def validate_enabled_param(formatter_name: str, value: str) -> None:
    """
    Ensure that enabled is True/False.

    In the past any truthy value was accepted which lead to unexpected behaviour.
    """
    # TODO: Replace it by type checking of parameters
    if value.lower() not in ("true", "false"):
        raise exceptions.InvalidParameterValueError(
            formatter_name, "enabled", value, "It should be 'true' or 'false'."
        ) from None


class RulesLoader:
    def __init__(
        self, rule_matcher: RuleMatcher, custom_rules: list[str], configure: list[str], silent: bool, config_source: str
    ) -> None:
        self.rule_matcher = rule_matcher
        self.custom_rules = custom_rules
        self.configurables = map_configure(configure)
        self.silent = silent
        self.base_checkers: list[BaseChecker] = []
        self.after_checkers: list[AfterRunChecker] = []
        self.project_checkers: list[ProjectChecker] = []
        self.rules: dict[str, Rule] = {}
        self.config_source = config_source

    def apply_configuration(self, rule: Rule, rule_name_or_id: str) -> None:
        if rule_name_or_id not in self.configurables:
            return
        if rule.deprecated:
            if not self.silent:
                print(rule.deprecation_warning)
            return
        for param_name, value in self.configurables[rule_name_or_id].items():
            rule.configure(param_name, value)

    def load_rules(self) -> None:
        robocop_importer = LinterImporter(external_rules_paths=self.custom_rules)
        for checker in robocop_importer.get_initialized_checkers():
            self.register_checker(checker)
        # linter.rules.update(robocop_importer.deprecated_rules)
        self.validate_any_rule_enabled()

    def register_checker(self, checker: BaseChecker | AfterRunChecker | ProjectChecker) -> None:
        any_enabled = False

        # map checker rules to global rules & check for disabled rule
        for rule_name_or_id, rule in checker.rules.items():
            self.apply_configuration(rule, rule_name_or_id)
            rule.enabled = self.rule_matcher.is_rule_enabled(rule)
            if rule.enabled:
                any_enabled = True
                rule.fixable = self.rule_matcher.is_rule_fixable(rule)
            self.rules[rule_name_or_id] = rule
            rule.checker = checker
        # if the checker does not have enabled rules, we skip it. Rules are registered anyway, for listing or docs
        if not any_enabled:  # let's not register disabled checkers
            return

        # split by the checker type
        if isinstance(checker, VisitorChecker):
            self.base_checkers.append(checker)
        elif isinstance(checker, AfterRunChecker):
            self.after_checkers.append(checker)
        elif isinstance(checker, ProjectChecker):
            self.project_checkers.append(checker)
        else:  # fail-safe
            self.base_checkers.append(checker)

    def validate_any_rule_enabled(self) -> None:
        """Validate and print a warning if no rule is selected."""
        if self.silent:
            return
        if not (self.base_checkers or self.after_checkers or self.project_checkers):
            print(
                f"No rule selected with the existing configuration from the {self.config_source} . "
                f"Please check if all rules from --select exist and there is no conflicting filter option."
            )


class FormattersLoader:
    def __init__(
        self,
        select: list[str],
        extend_select: list[str],
        configure: list[str],
        force_order: bool,
        allow_disabled: bool,
        target_version: Version,
        skip_config: SkipConfig,
        whitespace_config: WhitespaceConfig,
        languages: Languages | None,
    ) -> None:
        self.select = select
        self.extend_select = extend_select
        self.configurables = map_configure(configure)
        self.force_order = force_order
        self.allow_disabled = allow_disabled
        self.target_version = target_version
        self.skip_config = skip_config
        self.whitespace_config = whitespace_config
        self.languages = languages
        self.formatters: dict[str, Formatter] = {}

    def selected_formatters(self) -> list[str]:
        if not self.select:
            selected = FORMATTERS + self.extend_select
        elif not self.force_order:
            # first get default formatters in the same order as defined in robocop
            ordered_selected = [formatter for formatter in FORMATTERS if formatter in self.select]
            # then add any other formatters in select, in a given order
            ordered_selected.extend([formatter for formatter in self.select if formatter not in ordered_selected])
            selected = ordered_selected + self.extend_select
        else:
            selected = self.select + self.extend_select
        return list(dict.fromkeys(selected))  # remove duplicates, order is preserved

    def load_formatters(self) -> None:
        explicit_select: set[str] = set(self.select + self.extend_select)
        for formatter in self.selected_formatters():
            # formatter may be a single class or whole file / directory, so we need additional iterate
            for container in import_formatter(formatter, self.configurables, self.skip_config):
                overwritten = container.name in explicit_select or formatter in explicit_select
                if overwritten:
                    enabled = True
                elif "enabled" in container.args:
                    validate_enabled_param(container.name, container.args["enabled"])
                    enabled = container.args["enabled"].lower() == "true"
                else:
                    enabled = getattr(container.instance, "ENABLED", True)
                if not (enabled or self.allow_disabled):
                    continue
                enabled_in_version = can_run_in_robot_version(
                    container.instance, overwritten=overwritten, target_version=self.target_version.major
                )
                if not enabled_in_version and not self.allow_disabled:
                    continue
                container.instance.ENABLED = enabled_in_version and enabled
                container.instance.formatting_config = self.whitespace_config
                container.instance.formatters = self.formatters
                container.instance.languages = self.languages
                self.formatters[container.name] = container.instance


class ConfigResolver:
    def __init__(self, load_rules: bool = False, load_formatters: bool = False) -> None:
        self.load_rules = load_rules
        self.load_formatters = load_formatters
        self._resolved_configs: dict[str, ResolvedConfig] = {}

    def resolve_config(self, config: Config) -> ResolvedConfig:
        if config.hash in self._resolved_configs:
            return self._resolved_configs[config.hash]
        checkers: list[BaseChecker] = []
        after_run_checkers: list[AfterRunChecker] = []
        project_checkers: list[ProjectChecker] = []
        rules: dict[str, Rule] = {}
        formatters: dict[str, Formatter] = {}
        if self.load_rules:
            rule_matcher = RuleMatcher(
                config.linter.select,
                config.linter.extend_select,
                config.linter.ignore,
                config.linter.target_version,
                config.linter.threshold,
                config.linter.fixable,
                config.linter.unfixable,
            )
            loader = RulesLoader(
                rule_matcher, config.linter.custom_rules, config.linter.configure, config.silent, config.config_source
            )
            loader.load_rules()
            checkers = loader.base_checkers
            after_run_checkers = loader.after_checkers
            project_checkers = loader.project_checkers
            rules = loader.rules
        if self.load_formatters:
            formatters_loader = FormattersLoader(
                config.formatter.select,
                config.formatter.extend_select,
                config.formatter.configure,
                config.formatter.force_order,
                config.formatter.allow_disabled,
                config.formatter.target_version,
                config.formatter.skip_config,
                config.formatter.whitespace_config,
                config.languages,
            )
            formatters_loader.load_formatters()
            formatters = formatters_loader.formatters
        resolved_config = ResolvedConfig(checkers, after_run_checkers, project_checkers, rules, formatters)
        self._resolved_configs[config.hash] = resolved_config
        return resolved_config
