from __future__ import annotations

import os
from dataclasses import dataclass, field, fields
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

from robocop.linter.utils import ROBOT_VERSION

try:
    from robot.api import Languages  # RF 6.0
except ImportError:
    Languages = None
import pathspec
import typer
from typing_extensions import Self

from robocop import errors, files
from robocop.formatter import formatters
from robocop.formatter.skip import SkipConfig
from robocop.formatter.utils import misc  # TODO merge with linter misc
from robocop.linter import exceptions, rules
from robocop.linter.rules import BaseChecker, RuleSeverity
from robocop.linter.utils.misc import compile_rule_pattern
from robocop.linter.utils.version_matching import Version

CONFIG_NAMES = frozenset(("robocop.toml", "pyproject.toml", "robot.toml"))
DEFAULT_INCLUDE = frozenset(("*.robot", "*.resource"))
DEFAULT_EXCLUDE = frozenset((".direnv", ".eggs", ".git", ".svn", ".hg", ".nox", ".tox", ".venv", "venv", "dist"))

DEFAULT_ISSUE_FORMAT = "{source}:{line}:{col} [{severity}] {rule_id} {desc} ({name})"

if TYPE_CHECKING:
    import re
    from collections.abc import Generator

    from robocop.linter.rules import Rule


class RuleMatcher:
    def __init__(self, config: LinterConfig):
        self.config = config

    def is_rule_enabled(self, rule: Rule) -> bool:
        if self.is_rule_disabled(rule):
            return False
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
        return misc.ROBOT_VERSION.major
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
    if target_version > misc.ROBOT_VERSION.major:
        raise typer.BadParameter(
            f"Target Robot Framework version ({target_version}) should not be higher than "
            f"installed version ({misc.ROBOT_VERSION})."
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
    ignore: list[str] | None = field(default_factory=list)
    issue_format: str | None = DEFAULT_ISSUE_FORMAT
    target_version: Version | None = field(default=None, compare=False)
    threshold: RuleSeverity | None = RuleSeverity.INFO
    custom_rules: list[str] | None = field(default_factory=list)
    include_rules: set[str] | None = field(default_factory=set, compare=False)
    exclude_rules: set[str] | None = field(default_factory=set, compare=False)
    include_rules_patterns: set[re.Pattern] | None = field(default_factory=set, compare=False)
    exclude_rules_patterns: set[re.Pattern] | None = field(default_factory=set, compare=False)
    reports: list[str] | None = field(default_factory=list)
    persistent: bool | None = False
    compare: bool | None = False
    exit_zero: bool | None = False
    return_result: bool = False
    config_source: str = field(default="cli", compare=False)
    _checkers: list[BaseChecker] | None = field(default=None, compare=False)
    _rules: dict[str, Rule] | None = field(default=None, compare=False)

    def __post_init__(self):
        if not self.target_version:
            self.target_version = ROBOT_VERSION

    @property
    def checkers(self):
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

    def check_for_disabled_rules(self) -> None:
        """Check checker configuration to disable rules."""
        rule_matcher = RuleMatcher(self)
        for checker in self._checkers:
            if not self.any_rule_enabled(checker, rule_matcher):
                checker.disabled = True

    @staticmethod
    def any_rule_enabled(checker: type[BaseChecker], rule_matcher: RuleMatcher) -> bool:
        any_enabled = False
        for rule in checker.rules.values():
            rule.enabled = rule_matcher.is_rule_enabled(rule)
            if rule.enabled:
                any_enabled = True
        return any_enabled

    def validate_any_rule_enabled(self) -> None:
        """Validate and print warning if no rule is selected."""
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
                raise exceptions.ConfigGeneralError(
                    f"Provided invalid config: '{config}' (general pattern: <rule/report>.<param>=<value>)"
                ) from None
            if name in self._rules:
                rule = self._rules[name]
                if rule.deprecated:
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
            print(f"Unknown fields in the [robocop.lint] section: {unknown_fields}")
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


@dataclass
class FormatterConfig:
    whitespace_config: WhitespaceConfig = field(default_factory=WhitespaceConfig)
    select: list[str] | None = field(default_factory=list)
    custom_formatters: list[str] | None = field(default_factory=list)
    configure: list[str] | None = field(default_factory=list)
    force_order: bool | None = False
    allow_disabled: bool | None = False
    target_version: int | str | None = field(default=misc.ROBOT_VERSION.major, compare=False)
    skip_config: SkipConfig = field(default_factory=SkipConfig)
    overwrite: bool | None = False
    diff: bool | None = False
    output: Path | None = None  # TODO
    color: bool | None = False
    check: bool | None = False
    reruns: int | None = 0
    start_line: int | None = None
    end_line: int | None = None
    language: list[str] | None = field(default_factory=list)  # TODO: it is both part of common and formatter
    languages: Languages | None = field(default=None, compare=False)
    _parameters: dict[str, dict[str, str]] | None = field(default=None, compare=False)
    _formatters: dict[str, ...] | None = field(default=None, compare=False)

    @classmethod
    def from_toml(cls, config: dict, config_parent: Path) -> FormatterConfig:
        config_fields = {config_field.name for config_field in fields(cls) if config_field.compare}
        # TODO assert type (list vs list etc)
        override = {param: value for param, value in config.items() if param in config_fields}
        override["whitespace_config"] = WhitespaceConfig.from_toml(config)
        override["skip_config"] = SkipConfig.from_toml(config)
        if "custom_formatters" in override:
            override["custom_formatters"] = [
                resolve_relative_path(path, config_parent, ensure_exists=True) for path in config["custom_formatters"]
            ]
        known_fields = (
            config_fields
            | {config_field.name for config_field in fields(WhitespaceConfig)}
            | {
                f"skip_{config_field.name}" if not config_field.name.startswith("skip") else config_field.name
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

    def load_formatters(self):
        self._formatters = {}
        allow_version_mismatch = False
        self.load_languages()
        for formatter in self.selected_formatters():
            for container in formatters.import_formatter(formatter, self.combined_configure, self.skip_config):
                if container.name in self.select or formatter in self.select:
                    enabled = True
                elif "enabled" in container.args:
                    enabled = container.args["enabled"].lower() == "true"
                else:
                    enabled = getattr(container.instance, "ENABLED", True)
                if not (enabled or self.allow_disabled):
                    continue
                if formatters.can_run_in_robot_version(
                    container.instance,
                    overwritten=container.name in self.select,
                    target_version=self.target_version,
                ):
                    container.enabled_by_default = enabled
                    self._formatters[container.name] = container.instance
                elif allow_version_mismatch and self.allow_disabled:
                    container.instance.ENABLED = False
                    container.enabled_by_default = False
                    self._formatters[container.name] = container.instance
                container.instance.formatting_config = self.whitespace_config
                container.instance.formatters = self.formatters
                container.instance.languages = self.languages

    def selected_formatters(self) -> list[str]:
        if not self.select:
            return formatters.FORMATTERS + self.custom_formatters
        if not self.force_order:
            return self.ordered_select + self.custom_formatters
        return self.select + self.custom_formatters

    def load_languages(self) -> None:
        if Languages is not None:
            self.languages = Languages(self.language)

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
            raise errors.InvalidParameterFormatError(configure) from None
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
                if name not in self._parameters:
                    self._parameters[name] = {}
                self._parameters[name][param] = value
        return self._parameters


@dataclass
class FileFiltersOptions(ConfigContainer):
    include: set[str] | None = None
    default_include: set[str] | None = field(default_factory=lambda: DEFAULT_INCLUDE)
    exclude: set[str] | None = None
    default_exclude: set[str] | None = field(default_factory=lambda: DEFAULT_EXCLUDE)

    @classmethod
    def from_toml(cls, config: dict) -> FileFiltersOptions:
        filter_config = {}
        for key in ("include", "default_include", "exclude", "default_exclude"):
            if key in config:
                filter_config[key] = set(config.pop(key))
        return cls(**filter_config)

    def path_excluded(self, path: Path) -> bool:
        """Exclude all paths matching exclue patterns."""
        exclude_paths = set(self.default_exclude)
        if self.exclude:
            exclude_paths |= self.exclude
        return any(path.match(pattern) for pattern in exclude_paths)

    def path_included(self, path: Path) -> bool:
        """Only allow paths matching include patterns."""
        include_paths = set(self.default_include)
        if self.include:
            include_paths |= self.include
        return any(path.match(pattern) for pattern in include_paths)


@dataclass
class Config:
    sources: list[str] | None = field(default_factory=lambda: ["."])
    file_filters: FileFiltersOptions | None = field(default_factory=FileFiltersOptions)
    linter: LinterConfig | None = field(default_factory=LinterConfig)
    formatter: FormatterConfig | None = field(default_factory=FormatterConfig)
    language: list[str] | None = field(default_factory=list)
    verbose: bool | None = field(default_factory=bool)
    target_version: int | str | None = misc.ROBOT_VERSION.major
    config_source: str = "cli"

    def __post_init__(self) -> None:
        self.target_version = validate_target_version(self.target_version)
        if self.formatter:
            self.formatter.target_version = self.target_version
        if self.linter:
            self.linter.target_version = Version(f"{self.target_version}.0")

    @classmethod
    def from_toml(cls, config: dict, config_path: Path) -> Config:
        """
        Load configuration from toml dict.

        If there is parent configuration, use it to overwrite loaded configuration.
        """
        # TODO: validate all key and types
        Config.validate_config(config, config_path)
        parsed_config = {
            "config_source": str(config_path),
            "linter": LinterConfig.from_toml(config.pop("lint", {}), config_path),
            "file_filters": FileFiltersOptions.from_toml(config),
            "language": config.pop("language", []),
            "verbose": config.pop("verbose", False),
        }
        if "target_version" in config:
            parsed_config["target_version"] = validate_target_version(config["target_version"])
        parsed_config["formatter"] = FormatterConfig.from_toml(config.pop("format", {}), config_path.parent)
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
            "verbose",
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
            "include",
            "default_include",
            "exclude",
            "default_exclude",
            "target_version",
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
                "config_source",
            ):  # TODO Use field metadata
                continue
            value = getattr(overwrite_config, config_field.name)
            if value:
                setattr(self, config_field.name, value)
        if overwrite_config.linter:
            for config_field in fields(overwrite_config.linter):
                if config_field.name == "config_source":
                    continue
                value = getattr(overwrite_config.linter, config_field.name)
                if value:
                    if config_field.name == "reports":  # allows to combine cli and config for reports
                        self.linter.reports.extend(value)
                    else:
                        setattr(self.linter, config_field.name, value)
                        if config_field.name in {"select", "ignore"}:
                            self.linter.config_source = "cli"
        if overwrite_config.formatter:
            for config_field in fields(overwrite_config.formatter):
                if config_field.name in ("whitespace_config", "skip_config") or config_field.name.startswith("_"):
                    continue
                value = getattr(overwrite_config.formatter, config_field.name)
                if value:
                    setattr(self.formatter, config_field.name, value)
            self.formatter.whitespace_config.overwrite(overwrite_config.formatter.whitespace_config)
            self.formatter.skip_config.overwrite(overwrite_config.formatter.skip_config)
            self.formatter.language = self.language  # TODO
        self.file_filters.overwrite(overwrite_config.file_filters)

    def __str__(self):
        return str(self.config_source)


class GitIgnoreResolver:
    def __init__(self):
        self.cached_ignores: dict[Path, pathspec.PathSpec] = {}

    def path_excluded(self, path: Path, gitignores: list[tuple[Path, pathspec.PathSpec]]) -> bool:
        """Find path gitignores and check if file is excluded."""
        if not gitignores:
            return False
        for gitignore_path, gitignore in gitignores:
            relative_path = files.get_path_relative_to_path(path, gitignore_path)
            if gitignore.match_file(relative_path):
                return True
        return False

    def read_gitignore(self, path: Path) -> pathspec.PathSpec:
        """Return a PathSpec loaded from the file."""
        with path.open(encoding="utf-8") as gf:
            lines = gf.readlines()
        return pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern, lines)

    def resolve_path_ignores(self, path: Path) -> list[tuple[Path, pathspec.PathSpec]]:
        """
        Visit all parent directories and find all gitignores.

        Gitignores are cached for multiple sources.

        Args:
            path: path to file/directory

        Returns:
            PathSpec from merged gitignores.

        """
        # TODO: respect nogitignore flag
        if path.is_file():
            path = path.parent
        gitignores = []
        for parent_path in [path, *path.parents]:
            if parent_path in self.cached_ignores:
                gitignores.append(self.cached_ignores[parent_path])
            elif (gitignore_path := parent_path / ".gitignore").is_file():
                gitignore = self.read_gitignore(gitignore_path)
                self.cached_ignores[parent_path] = (parent_path, gitignore)
                gitignores.append((parent_path, gitignore))
            if (parent_path / ".git").is_dir():
                break
        return gitignores


class ConfigManager:
    """
    Finds and loads configuration files for each file.

    Config provided from cli takes priority. ``--config`` option overrides any found configuration file.
    """

    def __init__(
        self,
        sources: list[str] | None = None,
        config: Path | None = None,
        root: str | None = None,  # noqa: ARG002  TODO
        ignore_git_dir: bool = False,
        ignore_file_config: bool = False,
        skip_gitignore: bool = False,  # noqa: ARG002  TODO
        overwrite_config: Config | None = None,
    ):
        """
        Initialize ConfigManager.

        Args:
            sources: List of sources with Robot Framework files.
            config: Path to configuration file.
            root: Root of the project. Can be supplied if it's known beforehand (for example by IDE plugin)
            Otherwise it will be automatically found.
            ignore_git_dir: Flag for project root discovery to decide if directories with `.git` should be ignored.
            ignore_file_config: If set to True, Robocop will not load found configuration files
            skip_gitignore: Do not load .gitignore files when looking for the files to parse
            overwrite_config: Overwrite existing configuration file with the Config class

        """
        self.cached_configs: dict[Path, Config] = {}
        self.overwrite_config = overwrite_config
        self.ignore_git_dir = ignore_git_dir
        self.ignore_file_config = ignore_file_config
        self.gitignore_resolver = GitIgnoreResolver()
        self.overridden_config = (
            config is not None
        )  # TODO: what if both cli and --config? should take --config then apply cli
        self.root = Path.cwd()  # FIXME or just check if its fine
        self.default_config: Config = self.get_default_config(config)
        self.sources = sources
        self._paths: dict[Path, Config] | None = None

    @property
    def paths(self) -> Generator[tuple[Path, Config], None, None]:
        # TODO: what if we provide the same path twice - tests
        if self._paths is None:
            self._paths = {}
            sources = self.sources if self.sources else self.default_config.sources
            ignore_file_filters = bool(sources)
            self.resolve_paths(sources, gitignores=None, ignore_file_filters=ignore_file_filters)
            self.find_default_config()
        yield from self._paths.items()

    def find_default_config(self):
        """
        Find default config from all loaded configs and set it.

        Default configuration file is configuration closest to cwd. It's options are used for global-like
        settings such as reports or exit codes.

        """
        if not self.cached_configs:
            return self.default_config
        # look for path as cwd or any of parents of cwd
        cwd = Path.cwd()
        if cwd in self.cached_configs:
            return self.cached_configs[cwd]
        for parent in cwd.parents:
            if parent in self.cached_configs:
                return self.cached_configs[parent]
        return self.default_config

    def get_default_config(self, config_path: Path | None) -> Config:
        """Get default config either from --config option or from the cli."""
        if config_path:
            configuration = files.read_toml_config(config_path)
            config = Config.from_toml(configuration, config_path)
        else:
            config = Config()
        config.overwrite_from_config(self.overwrite_config)
        return config

    def is_git_project_root(self, path: Path) -> bool:
        """Check if current directory contains .git directory and might be a project root."""
        if self.ignore_git_dir:
            return False
        return (path / ".git").is_dir()

    def find_closest_config(self, source: Path) -> Config:
        """Look in the directory and its parents for the closest valid configuration file."""
        # we always look for configuration in parent directory, unless we hit the top already
        if not self.is_git_project_root(source) and source.parents:
            source = source.parent
        check_dirs = [source, *source.parents]
        seen = []  # if we find config, mark all visited directories with resolved config
        for check_dir in check_dirs:
            if check_dir in self.cached_configs:
                return self.cached_configs[check_dir]
            seen.append(check_dir)
            for config_filename in CONFIG_NAMES:
                if (config_path := (check_dir / config_filename)).is_file():
                    configuration = files.read_toml_config(config_path)
                    if configuration is not None:
                        config = Config.from_toml(configuration, config_path)
                        config.overwrite_from_config(self.overwrite_config)  # TODO those two lines together
                        self.cached_configs.update({sub_dir: config for sub_dir in seen})
                        if config.verbose:
                            print(f"Loaded {config_path} configuration file.")
                        return config
            if self.is_git_project_root(check_dir):
                break
        return self.default_config

    def get_config_for_source_file(self, source_file: Path) -> Config:
        """
        Find the closest config to the source file or directory.

        If it was loaded before it will be returned from the cache. Otherwise, we will load it and save it to cache
        first.

        Args:
            source_file: Path to Robot Framework source file or directory.

        """
        if self.overridden_config or self.ignore_file_config:
            return self.default_config
        return self.find_closest_config(source_file)

    def resolve_paths(
        self,
        sources: list[str | Path],
        gitignores: list[tuple[Path, pathspec.PathSpec]] | None,
        ignore_file_filters: bool = False,
    ) -> None:
        """
        Find all files to parse and their corresponding configs.

        Initially sources can be ["."] (if not path provided, assume current working directory).
        It can be also any list of paths, for example ["tests/", "file.robot"].

        Args:
            sources: list of sources from CLI or configuration file.
            gitignores: list of gitignore pathspec and their locations for path resolution.
            ignore_file_filters: force robocop to parse file even if it's excluded in the configuration

        """
        for source in sources:
            source = Path(source).resolve()
            if source in self._paths:
                continue
            if not source.exists():  # TODO only for passed sources
                raise errors.FileError(source)
            if gitignores is None:
                source_gitignore = self.gitignore_resolver.resolve_path_ignores(source)
            else:
                source_gitignore = gitignores
            config = self.get_config_for_source_file(source)
            if not ignore_file_filters:
                if config.file_filters.path_excluded(source):
                    continue
                if source.is_file() and not config.file_filters.path_included(source):
                    continue
            if self.gitignore_resolver.path_excluded(source, source_gitignore):
                continue
            if source.is_dir():
                self.resolve_paths(source.iterdir(), gitignores)
            elif source.is_file():
                self._paths[source] = config
