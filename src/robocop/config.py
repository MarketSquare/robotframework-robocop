from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field, fields
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

from robot.errors import DataError

try:
    from robot.api import Languages  # RF 6.0
except ImportError:
    Languages = None
import typer
from typing_extensions import Self

from robocop import exceptions
from robocop.formatter import formatters
from robocop.formatter.skip import SkipConfig
from robocop.linter import rules
from robocop.linter.rules import (
    AfterRunChecker,
    BaseChecker,
    ProjectChecker,
    RuleSeverity,
)
from robocop.linter.utils.misc import compile_rule_pattern
from robocop.version_handling import ROBOT_VERSION, Version

DEFAULT_INCLUDE = frozenset(("*.robot", "*.resource"))
DEFAULT_EXCLUDE = frozenset((".direnv", ".eggs", ".git", ".svn", ".hg", ".nox", ".tox", ".venv", "venv", "dist"))

DEFAULT_ISSUE_FORMAT = "{source}:{line}:{col} [{severity}] {rule_id} {desc} ({name})"

if TYPE_CHECKING:
    import re

    from robocop.linter.rules import Rule


class RuleMatcher:
    def __init__(self, config: LinterConfig):
        self.config = config

    def is_rule_enabled(self, rule: Rule) -> bool:  # noqa: PLR0911
        if self.is_rule_disabled(rule):
            return False
        if "ALL" in self.config.include_rules:
            return True
        if self.config.extend_include_rules or self.config.extend_include_rules_patterns:
            if (
                rule.rule_id in self.config.extend_include_rules
                or rule.name in self.config.extend_include_rules_patterns
            ):
                return True
            if any(
                pattern.match(rule.rule_id) or pattern.match(rule.name)
                for pattern in self.config.include_rules_patterns
            ):
                return True
        if (
            self.config.include_rules or self.config.include_rules_patterns
        ):  # if any include pattern, it must match with something
            if rule.rule_id in self.config.include_rules or rule.name in self.config.include_rules:
                return True
            return any(
                pattern.match(rule.rule_id) or pattern.match(rule.name)
                for pattern in self.config.include_rules_patterns
            )
        return rule.enabled

    def is_rule_disabled(self, rule: Rule) -> bool:
        if rule.is_disabled(self.config.target_version):
            return True
        if rule.severity < self.config.threshold and not rule.config.get("severity_threshold"):
            return True
        if rule.rule_id in self.config.exclude_rules or rule.name in self.config.exclude_rules:
            return True
        return any(
            pattern.match(rule.rule_id) or pattern.match(rule.name) for pattern in self.config.exclude_rules_patterns
        )


@dataclass
class ConfigContainer:
    def overwrite(self, other: Self) -> None:
        """
        Overwrite options loaded from configuration or default options with config from cli.

        If other has value set to None, it was never set and can be ignored.
        """
        if not other:
            return
        for config_field in fields(other):
            value = getattr(other, config_field.name)
            if value is not None:
                setattr(self, config_field.name, value)


@dataclass
class WhitespaceConfig(ConfigContainer):
    space_count: int | str | None = 4
    indent: int | str | None = None
    continuation_indent: int | str | None = None
    line_ending: str | None = "native"
    separator: str | None = "space"
    line_length: int | None = 120

    @classmethod
    def from_toml(cls, config: dict) -> WhitespaceConfig:
        config_fields = {config_field.name for config_field in fields(cls)}
        override = {param: value for param, value in config.items() if param in config_fields}
        return cls(**override)

    def process_config(self):
        """Prepare config with processed values. If value is missing, use related config as a default."""
        if self.indent is None:
            self.indent = self.space_count
        if self.continuation_indent is None:
            self.continuation_indent = self.space_count
        if self.separator == "space":
            self.separator = " " * self.space_count
            self.indent = " " * self.indent
            self.continuation_indent = " " * self.continuation_indent
        elif self.separator == "tab":
            self.separator = "\t"
            self.indent = "\t"
            self.continuation_indent = "\t"
        if self.line_ending == "native":
            self.line_ending = os.linesep
        elif self.line_ending == "windows":
            self.line_ending = "\r\n"
        elif self.line_ending == "unix":
            self.line_ending = "\n"


def parse_rule_severity(value: str):
    return RuleSeverity.parser(value, rule_severity=False)


class TargetVersion(Enum):
    RF4 = "4"
    RF5 = "5"
    RF6 = "6"
    RF7 = "7"


def validate_target_version(value: str | TargetVersion | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, TargetVersion):
        target_version = int(value.value)
    else:
        try:
            target_version = int(TargetVersion[f"RF{value}"].value)
        except KeyError:
            versions = ", ".join(ver.value for ver in TargetVersion)
            raise typer.BadParameter(
                f"Invalid target Robot Framework version: '{value}' is not one of {versions}"
            ) from None
    if target_version > ROBOT_VERSION.major:
        raise typer.BadParameter(
            f"Target Robot Framework version ({target_version}) should not be higher than "
            f"installed version ({ROBOT_VERSION})."
        ) from None
    return target_version


def resolve_relative_path(orig_path: str, config_dir: Path, ensure_exists: bool) -> str:
    """
    Resolve a given path relative to a configuration directory.

    If the path is absolute, it is returned as-is. If the path is relative, it is resolved
    relative to `config_dir`. Optionally, the method can ensure the resolved path exists
    before returning it.
    """
    path = Path(orig_path)
    if path.is_absolute():
        return orig_path
    resolved_path = config_dir / path
    if not ensure_exists or resolved_path.exists():
        return str(resolved_path)
    return orig_path


@dataclass
class LinterConfig:
    configure: list[str] | None = field(default_factory=list)
    select: list[str] | None = field(default_factory=list)
    extend_select: list[str] | None = field(default_factory=list)
    ignore: list[str] | None = field(default_factory=list)
    per_file_ignores: dict[str, list[str]] | None = field(default=None)
    issue_format: str | None = DEFAULT_ISSUE_FORMAT
    target_version: Version | None = field(default=None, compare=False)
    threshold: RuleSeverity | None = RuleSeverity.INFO
    custom_rules: list[str] | None = field(default_factory=list)
    include_rules: set[str] | None = field(default_factory=set, compare=False)
    extend_include_rules: set[str] | None = field(default_factory=set, compare=False)
    exclude_rules: set[str] | None = field(default_factory=set, compare=False)
    include_rules_patterns: set[re.Pattern] | None = field(default_factory=set, compare=False)
    extend_include_rules_patterns: set[re.Pattern] | None = field(default_factory=set, compare=False)
    exclude_rules_patterns: set[re.Pattern] | None = field(default_factory=set, compare=False)
    reports: list[str] | None = field(default_factory=list)
    persistent: bool | None = False
    compare: bool | None = False
    exit_zero: bool | None = False
    return_result: bool = False
    config_source: str = field(default="cli", compare=False)
    _checkers: list[BaseChecker] | None = field(default=None, compare=False)
    after_run_checkers: list[AfterRunChecker] | None = field(default=None, compare=False)
    project_checkers: list[BaseChecker] | None = field(default=None, compare=False)
    _rules: dict[str, Rule] | None = field(default=None, compare=False)
    silent: bool | None = False

    def __post_init__(self):
        if not self.target_version:
            self.target_version = ROBOT_VERSION

    @property
    def checkers(self) -> list[BaseChecker]:
        if self._checkers is None:
            self.load_configuration()
        return self._checkers

    @property
    def rules(self):
        if self._rules is None:
            self.load_configuration()
        return self._rules

    def load_configuration(self):
        """Load rules, checkers and their configuration."""
        self.split_inclusions_exclusions_into_patterns()
        self.load_checkers()
        self.configure_rules()
        self.check_for_disabled_rules()
        self.validate_any_rule_enabled()
        self.split_checkers_by_type()

    def load_checkers(self) -> None:
        """
        Initialize checkers and rules containers and start rules discovery.

        Instance of this class is passed over since it will be used to populate checkers/rules containers.
        Additionally, rules can also refer to instance of this class to access config class.
        """
        self._checkers = []
        self._rules = {}
        rules.init(self)

    def register_checker(self, checker: type[BaseChecker]) -> None:  # [type[BaseChecker]]
        for rule_name_or_id, rule in checker.rules.items():
            self._rules[rule_name_or_id] = rule
        self._checkers.append(checker)

    def split_checkers_by_type(self) -> None:
        """
        Split checkers by type.

        Prepare checkers containers so they can be iterated separately depending on the type.
        Most checkers (VisitorChecker, RawFileChecker) are used when scanning the file. Some may be used after
        all other checkers finish scanning (AfterRunChecker) or after all files finish scanning (ProjectChecker).
        """
        base_checkers, after_checkers, project_checkers = [], [], []
        for checker in self._checkers:
            if isinstance(checker, AfterRunChecker):
                after_checkers.append(checker)
            elif isinstance(checker, ProjectChecker):
                project_checkers.append(checker)
            else:
                base_checkers.append(checker)
        self._checkers = base_checkers
        self.after_run_checkers = after_checkers
        self.project_checkers = project_checkers

    def check_for_disabled_rules(self) -> None:
        """Check checker configuration to disable rules."""
        rule_matcher = RuleMatcher(self)
        for checker in self._checkers:
            if not self.any_rule_enabled(checker, rule_matcher):
                checker.disabled = True

    @staticmethod
    def any_rule_enabled(checker: type[BaseChecker], rule_matcher: RuleMatcher) -> bool:
        any_enabled = False
        # TODO: rules contain rule_id: rule and rule_name: rule so we are checking the same rule twice
        for rule in checker.rules.values():
            rule.enabled = rule_matcher.is_rule_enabled(rule)
            if rule.enabled:
                any_enabled = True
        return any_enabled

    def validate_any_rule_enabled(self) -> None:
        """Validate and print warning if no rule is selected."""
        if self.silent:
            return
        if not any(not checker.disabled for checker in self._checkers):
            print(
                f"No rule selected with the existing configuration from the {self.config_source} . "
                f"Please check if all rules from --select exist and there is no conflicting filter option."
            )

    def configure_rules(self) -> None:
        """
        Iterate over configuration for rules and reports and apply it.

        Accepted format is rule_name.param=value or report_name.param=value . ``rule_id`` can be used instead of
        ``rule_name``.
        """
        for config in self.configure:
            try:
                name, param_and_value = config.split(".", maxsplit=1)
                param, value = param_and_value.split("=", maxsplit=1)
            except ValueError:
                raise exceptions.InvalidConfigurationFormatError(config) from None
            if name in self._rules:
                rule = self._rules[name]
                if rule.deprecated:
                    if not self.silent:
                        print(rule.deprecation_warning)
                else:
                    rule.configure(param, value)
            # else:  TODO
            #     raise exceptions.RuleOrReportDoesNotExist(name, self._rules)

    def split_inclusions_exclusions_into_patterns(self):
        if self.select:
            for rule in self.select:
                if "*" in rule:
                    self.include_rules_patterns.add(compile_rule_pattern(rule))
                else:
                    self.include_rules.add(rule)
        if self.extend_select:
            for rule in self.extend_select:
                if "*" in rule:
                    self.extend_include_rules_patterns.add(compile_rule_pattern(rule))
                else:
                    self.extend_include_rules.add(rule)
        if self.ignore:
            for rule in self.ignore:
                if "*" in rule:
                    self.exclude_rules_patterns.add(compile_rule_pattern(rule))
                else:
                    self.exclude_rules.add(rule)

    #     def validate_rules_exists_and_not_deprecated(self, rules: dict[str, "Rule"]):
    #         for rule in chain(self.include, self.exclude):
    #             if rule not in rules:
    #                 raise exceptions.RuleDoesNotExist(rule, rules) from None
    #             rule_def = rules[rule]
    #             if rule_def.deprecated:
    #                 print(rule_def.deprecation_warning)

    @classmethod
    def from_toml(cls, config: dict, config_path: Path) -> LinterConfig:
        config_fields = {config_field.name for config_field in fields(cls) if config_field.compare}
        # TODO assert type (list vs list etc)
        if unknown_fields := {param: value for param, value in config.items() if param not in config_fields}:
            print(f"Unknown fields in the [tool.robocop.lint] section: {unknown_fields}")
            raise typer.Exit(code=1)
        override = {param: value for param, value in config.items() if param in config_fields}
        if "threshold" in config:
            override["threshold"] = parse_rule_severity(config["threshold"])
        if "custom_rules" in config:
            override["custom_rules"] = [
                resolve_relative_path(path, config_path.parent, ensure_exists=True) for path in config["custom_rules"]
            ]
        override["config_source"] = str(config_path)
        return cls(**override)

    def __hash__(self) -> int:
        """
        Hash of configuration options that affect linting results.

        Used for cache invalidation - if configuration changes, cached results are invalidated.
        Note: This makes LinterConfig usable as dict key, but only hash config-affecting fields.

        Uses stable hashing (SHA256) to ensure consistent hashes across Python process restarts,
        avoiding issues with Python's hash randomization (PEP 456).

        Returns:
            Hash value of the configuration options.

        """

        def _sorted_tuple(items: list[str] | None) -> tuple[str, ...]:
            """
            Convert list to sorted tuple, handling None.

            Returns:
                A sorted tuple representation of the input list.

            """
            return tuple(sorted(items or []))

        def _per_file_ignores_str() -> str:
            """
            Create string representation of per_file_ignores.

            Returns:
                A string representation of per_file_ignores or empty string if None.

            """
            if not self.per_file_ignores:
                return ""
            items = sorted((key, ":".join(sorted(values))) for key, values in self.per_file_ignores.items())
            return ";".join(f"{key}={values}" for key, values in items)

        # Build a stable string representation of the config
        config_parts = [
            ":".join(_sorted_tuple(self.select)),
            ":".join(_sorted_tuple(self.extend_select)),
            ":".join(_sorted_tuple(self.ignore)),
            ":".join(_sorted_tuple(self.configure)),
            ":".join(_sorted_tuple(self.custom_rules)),
            str(self.threshold),
            str(self.target_version),
            _per_file_ignores_str(),
        ]
        config_str = "|".join(config_parts)

        # Use SHA256 for stable hashing, then convert to int for __hash__ return type
        hash_bytes = hashlib.sha256(config_str.encode("utf-8")).digest()
        # Convert first 8 bytes to int for hash compatibility
        return int.from_bytes(hash_bytes[:8], byteorder="big", signed=True)


@dataclass
class FormatterConfig:
    whitespace_config: WhitespaceConfig = field(default_factory=WhitespaceConfig)
    select: list[str] | None = field(default_factory=list)
    extend_select: list[str] | None = field(default_factory=list)
    configure: list[str] | None = field(default_factory=list)
    force_order: bool | None = False
    allow_disabled: bool | None = False
    target_version: int | str | None = field(default=ROBOT_VERSION.major, compare=False)
    skip_config: SkipConfig = field(default_factory=SkipConfig)
    overwrite: bool | None = None
    diff: bool | None = False
    output: Path | None = None  # TODO
    color: bool | None = True
    check: bool | None = False
    reruns: int | None = 0
    start_line: int | None = None
    end_line: int | None = None
    languages: Languages | None = field(default=None, compare=False)
    silent: bool | None = False
    return_result: bool = False
    _parameters: dict[str, dict[str, str]] | None = field(default=None, compare=False)
    _formatters: dict[str, ...] | None = field(default=None, compare=False)

    @property
    def overwrite_files(self) -> bool:
        if self.overwrite is not None:
            return self.overwrite
        return not self.check

    @classmethod
    def from_toml(cls, config: dict, config_parent: Path) -> FormatterConfig:
        config_fields = {config_field.name for config_field in fields(cls) if config_field.compare}
        # TODO assert type (list vs list etc)
        override = {param: value for param, value in config.items() if param in config_fields}
        override["whitespace_config"] = WhitespaceConfig.from_toml(config)
        override["skip_config"] = SkipConfig.from_toml(config)
        if "extend_select" in override:
            override["extend_select"] = [
                resolve_relative_path(path, config_parent, ensure_exists=True) for path in config["extend_select"]
            ]
        known_fields = (
            config_fields
            | {config_field.name for config_field in fields(WhitespaceConfig)}
            | {
                (f"skip_{config_field.name}" if not config_field.name.startswith("skip") else config_field.name)
                for config_field in fields(SkipConfig)
            }
        )
        if unknown_fields := {param: value for param, value in config.items() if param not in known_fields}:
            print(f"Unknown fields in the [robocop.format] section: {unknown_fields}")
            raise typer.Exit(code=1)
        return cls(**override)

    @property
    def formatters(self) -> dict[str, ...]:
        if self._formatters is None:
            self.whitespace_config.process_config()
            self.load_formatters()
        return self._formatters

    def is_formatter_selected(self, name: str, formatter: str):
        # TODO: have name and formatter name are different?
        return name in self.select or formatter in self.select

    def load_formatters(self):
        self._formatters = {}
        for formatter in self.selected_formatters():
            for container in formatters.import_formatter(formatter, self.combined_configure, self.skip_config):
                overwritten = self.is_formatter_selected(container.name, formatter)
                if overwritten:
                    enabled = True
                elif "enabled" in container.args:
                    enabled = container.args["enabled"].lower() == "true"
                else:
                    enabled = getattr(container.instance, "ENABLED", True)
                if not (enabled or self.allow_disabled):
                    continue
                if formatters.can_run_in_robot_version(
                    container.instance,
                    overwritten=overwritten,
                    target_version=self.target_version,
                ):
                    container.instance.ENABLED = enabled
                    self._formatters[container.name] = container.instance
                elif self.allow_disabled:
                    container.instance.ENABLED = False
                    self._formatters[container.name] = container.instance
                container.instance.formatting_config = self.whitespace_config
                container.instance.formatters = self.formatters
                container.instance.languages = self.languages

    def selected_formatters(self) -> list[str]:
        if not self.select:
            selected = formatters.FORMATTERS + self.extend_select
        elif not self.force_order:
            selected = self.ordered_select + self.extend_select
        else:
            selected = self.select + self.extend_select
        return list(dict.fromkeys(selected))  # remove duplicates

    @property
    def ordered_select(self) -> list[str]:
        """
        Order formatter names from --select using default formatters list.

        Custom formatters are put last.
        """
        selected = [formatter for formatter in formatters.FORMATTERS if formatter in self.select]
        selected.extend([formatter for formatter in self.select if formatter not in selected])
        return selected

    def _parse_configure(self, configure: str) -> tuple[str, str, str]:
        try:
            name, param_value = configure.split(".", maxsplit=1)
            param, value = param_value.split("=", maxsplit=1)
            name, param, value = name.strip(), param.strip(), value.strip()
        except ValueError:
            raise exceptions.InvalidConfigurationFormatError(configure) from None
        return name, param, value

    @property
    def combined_configure(self) -> dict[str, dict[str, str]]:
        """
        Aggregate configure for formatters and their parameters.

        For example:

            robocop format -c MyFormatter.param=value -c MyFormatter2.param=value -c MyFormatter.param=value

        will return:

            {"MyFormatter": {"param": "value", "param2": "value"}, "MyFormatter2": {"param": "value"}}

        Returns:
            Map of formatters and their parameters.

        """
        if self._parameters is None:
            self._parameters = {}
            for config in self.configure:
                name, param, value = self._parse_configure(config)
                # since enabled is not part of formatter args we need to validate it here
                if param == "enabled" and value.lower() not in ("false", "true"):
                    raise exceptions.InvalidParameterValueError(
                        name, "enabled", value, "It should be 'true' or 'false'."
                    ) from None
                if name not in self._parameters:
                    self._parameters[name] = {}
                self._parameters[name][param] = value
        return self._parameters

    def __hash__(self) -> int:
        """
        Hash of configuration options that affect formatting results.

        Used for cache invalidation - if configuration changes, cached results are invalidated.
        Note: This makes FormatterConfig usable as dict key, but only hash config-affecting fields.

        Uses stable hashing (SHA256) to ensure consistent hashes across Python process restarts,
        avoiding issues with Python's hash randomization (PEP 456).

        Returns:
            Hash value of the configuration options.

        """

        def _sorted_tuple(items: list[str] | None) -> tuple[str, ...]:
            """
            Convert list to sorted tuple, handling None.

            Returns:
                tuple: A sorted tuple representation of the input list.

            """
            return tuple(sorted(items or []))

        wc = self.whitespace_config
        # Build a stable string representation of the config
        config_parts = [
            ":".join(_sorted_tuple(self.select)),
            ":".join(_sorted_tuple(self.extend_select)),
            ":".join(_sorted_tuple(self.configure)),
            str(self.target_version),
            str(wc.space_count),
            str(wc.indent),
            str(wc.continuation_indent),
            str(wc.separator),
            str(wc.line_ending),
            str(wc.line_length),
        ]
        config_str = "|".join(config_parts)

        # Use SHA256 for stable hashing, then convert to int for __hash__ return type
        hash_bytes = hashlib.sha256(config_str.encode("utf-8")).digest()
        # Convert first 8 bytes to int for hash compatibility
        return int.from_bytes(hash_bytes[:8], byteorder="big", signed=True)


@dataclass
class CacheConfig:
    """Configuration for file-level caching."""

    enabled: bool | None = True
    cache_dir: Path | None = None

    @classmethod
    def from_toml(cls, config: dict, config_parent: Path) -> CacheConfig:
        """
        Create CacheConfig from TOML dictionary.

        Returns:
            CacheConfig: An instance of CacheConfig created from the provided TOML dictionary.

        """
        enabled = config.pop("cache", True)
        cache_dir = config.pop("cache_dir", None)
        if cache_dir is not None:
            cache_dir = Path(cache_dir)
            if not cache_dir.is_absolute():
                cache_dir = config_parent / cache_dir
        return cls(enabled=enabled, cache_dir=cache_dir)

    def overwrite_from_config(self, overwrite_config: Self) -> None:
        """Overwrite configuration with optional values from CLI."""
        if overwrite_config.cache_dir is not None:
            self.cache_dir = overwrite_config.cache_dir
            self.enabled = True
        elif overwrite_config.enabled is not None:
            self.enabled = overwrite_config.enabled


@dataclass
class FileFiltersOptions(ConfigContainer):
    include: set[str] | None = field(default_factory=set)
    default_include: set[str] | None = field(default_factory=lambda: DEFAULT_INCLUDE)
    exclude: set[str] | None = field(default_factory=set)
    default_exclude: set[str] | None = field(default_factory=lambda: DEFAULT_EXCLUDE)
    _included_paths: set[str] | None = field(default=None, compare=False)
    _excluded_paths: set[str] | None = field(default=None, compare=False)

    @property
    def included_paths(self) -> set[str]:
        if self._included_paths is None:
            self._included_paths = set(self.default_include).union(set(self.include))
        return self._included_paths

    @property
    def excluded_paths(self) -> set[str]:
        if self._excluded_paths is None:
            self._excluded_paths = set(self.default_exclude).union(set(self.exclude))
        return self._excluded_paths

    @classmethod
    def from_toml(cls, config: dict) -> FileFiltersOptions:
        filter_config = {}
        for key in ("include", "default_include", "exclude", "default_exclude"):
            if key in config:
                filter_config[key] = set(config.pop(key))
        return cls(**filter_config)

    def path_excluded(self, path: Path) -> bool:
        """Exclude all paths matching exclude patterns."""
        return any(path.match(pattern) for pattern in self.excluded_paths)

    def path_included(self, path: Path) -> bool:
        """Only allow paths matching include patterns."""
        return any(path.match(pattern) for pattern in self.included_paths)


def normalize_config_keys(config: dict[str, ...]) -> dict[str, ...]:
    """Allow to use target_version and target-version alternative names in configuration file."""
    return {key.replace("-", "_"): value for key, value in config.items()}


@dataclass
class Config:
    sources: list[str] | None = field(default_factory=lambda: ["."])
    file_filters: FileFiltersOptions | None = field(default_factory=FileFiltersOptions)
    linter: LinterConfig | None = field(default_factory=LinterConfig)
    formatter: FormatterConfig | None = field(default_factory=FormatterConfig)
    cache: CacheConfig | None = field(default_factory=CacheConfig)
    language: list[str] | None = field(default_factory=list)
    languages: Languages | None = field(default=None, compare=False)
    verbose: bool | None = field(default_factory=bool)
    silent: bool | None = field(default_factory=bool)
    target_version: int | str | None = ROBOT_VERSION.major
    _hash: int | None = None
    config_source: str = "cli"

    def __post_init__(self) -> None:
        self.target_version = validate_target_version(self.target_version)
        self.load_languages()
        if self.formatter:
            self.formatter.target_version = self.target_version or ROBOT_VERSION.major
            self.formatter.languages = self.languages
            self.formatter.silent = self.silent
        if self.linter:
            self.linter.target_version = Version(f"{self.target_version}.0") if self.target_version else ROBOT_VERSION
            self.linter.silent = self.silent

    def load_languages(self):
        if Languages is None:
            return
        try:
            self.languages = Languages(self.language)
        except DataError:
            languages = ", ".join(self.language)
            print(
                f"Failed to load languages: {languages}. "
                f"Verify if language is one of the supported languages: "
                f"https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#translations"
            )
            raise typer.Exit(code=1) from None

    @classmethod
    def from_toml(cls, config: dict, config_path: Path) -> Config:
        """
        Load configuration from toml dict.

        If there is parent configuration, use it to overwrite loaded configuration.
        """
        # TODO: validate all key and types
        config = normalize_config_keys(config)
        Config.validate_config(config, config_path)
        parsed_config = {
            "config_source": str(config_path),
            "linter": LinterConfig.from_toml(normalize_config_keys(config.pop("lint", {})), config_path),
            "file_filters": FileFiltersOptions.from_toml(config),
            "cache": CacheConfig.from_toml(config, config_path.parent),
            "language": config.pop("language", []),
            "verbose": config.pop("verbose", False),
            "silent": config.pop("silent", False),
        }
        if "target_version" in config:
            parsed_config["target_version"] = validate_target_version(config["target_version"])
        parsed_config["formatter"] = FormatterConfig.from_toml(
            normalize_config_keys(config.pop("format", {})), config_path.parent
        )
        parsed_config = {key: value for key, value in parsed_config.items() if value is not None}
        return cls(**parsed_config)

    @staticmethod
    def validate_config(config: dict, config_path: Path) -> None:
        old_options = {  # some options were deprecated, but most were moved into subdict (lint)
            "reports",
            "filetypesignore",
            "ignore_default",
            "threshold",
            "no_recursive",
            "persistent",
            "ext_rules",
            "configure",
            "output",
            "paths",
            "robotidy",
        }
        if isinstance(config.get("format", {}), str) or any(key in old_options for key in config):
            print(
                f"Configuration file seems to use Robocop < 6.0.0 or Robotidy syntax. "
                f"Please migrate the config: {config_path}"
            )
            raise typer.Exit(code=1)
        known_keys = {
            "lint",
            "format",
            "language",
            "verbose",
            "silent",
            "include",
            "default_include",
            "exclude",
            "default_exclude",
            "force_exclude",
            "target_version",
            "skip_gitignore",
            "extends",
            "cache",
            "cache_dir",
        }
        for key in config:
            if key not in known_keys:
                print(f"Unknown configuration key: '{key}' in {config_path}")
                raise typer.Exit(code=1)

    def overwrite_from_config(self, overwrite_config: Config | None) -> None:
        if not overwrite_config:
            return
        for config_field in fields(overwrite_config):
            if config_field.name in (
                "linter",
                "formatter",
                "file_filters",
                "cache",
                "config_source",
            ):  # TODO Use field metadata
                continue
            value = getattr(overwrite_config, config_field.name)
            if value:
                setattr(self, config_field.name, value)
        # Handle cache config - CLI cache settings override file config
        if overwrite_config.cache is not None:
            self.cache.overwrite_from_config(overwrite_config.cache)
        if overwrite_config.linter:
            for config_field in fields(overwrite_config.linter):
                if config_field.name == "config_source":
                    continue
                value = getattr(overwrite_config.linter, config_field.name)
                if value is not None:
                    if config_field.name == "reports":  # allows to combine cli and config for reports
                        self.linter.reports.extend(value)
                    elif config_field.name == "configure":
                        self.linter.configure.extend(value)
                    else:
                        setattr(self.linter, config_field.name, value)
                        if config_field.name in {"select", "ignore"}:
                            self.linter.config_source = "cli"
        if overwrite_config.formatter:
            for config_field in fields(overwrite_config.formatter):
                if config_field.name in (
                    "whitespace_config",
                    "skip_config",
                ) or config_field.name.startswith("_"):
                    continue
                value = getattr(overwrite_config.formatter, config_field.name)
                if value is not None:
                    if config_field.name == "configure":
                        self.formatter.configure.extend(value)
                    else:
                        setattr(self.formatter, config_field.name, value)
            self.formatter.whitespace_config.overwrite(overwrite_config.formatter.whitespace_config)
            self.formatter.skip_config.overwrite(overwrite_config.formatter.skip_config)
            self.formatter.languages = self.languages
        self.file_filters.overwrite(overwrite_config.file_filters)

    def __str__(self):
        return str(self.config_source)

    def hash(self) -> str:
        """
        Compute cache key combining linter config hash with language.

        Uses SHA256 for stable hashing across Python processes, unlike the built-in
        hash() which can vary due to hash randomization (PEP 456).

        Returns:
            str: The computed cache key as a hexadecimal digest.

        """
        if self._hash is None:
            hasher = hashlib.sha256()
            # Hash the linter config
            hasher.update(str(hash(self.linter)).encode("utf-8"))
            # Hash the language configuration (affects parsing)
            language_str = ":".join(sorted(self.language or []))
            hasher.update(language_str.encode("utf-8"))
            self._hash = hasher.hexdigest()
        return self._hash
