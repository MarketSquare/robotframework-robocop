from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path
from typing import TYPE_CHECKING, Any

try:
    from robot.api import Languages  # RF 6.0
except ImportError:
    Languages = None
import typer

from robocop.config.parser import (
    TargetVersion,
    normalize_config_keys,
    parse_rule_severity,
    resolve_relative_path,
    validate_old_config,
)

if TYPE_CHECKING:
    from robocop.linter.rules import RuleSeverity
    from robocop.version_handling import Version


def validate_config_fields(config_dict: dict[str, Any], known_fields: set[str], config_path: Path) -> None:
    if unknown_fields := {name for name in config_dict if name not in known_fields}:
        unknown_fields_str = ", ".join(f"'{field_name}'" for field_name in unknown_fields)
        print(f"Unknown configuration key: {unknown_fields_str} in {config_path} .")
        raise typer.Exit(code=1)


@dataclass
class RawWhitespaceConfig:
    space_count: int | None = None
    indent: int | None = None
    continuation_indent: int | None = None
    line_ending: str | None = None
    separator: str | None = None
    line_length: int | None = None

    @classmethod
    def from_dict(cls, config_dict: dict[str, Any]) -> RawWhitespaceConfig:
        # fields are validated in parent
        config_fields = {config_field.name for config_field in fields(cls)}
        override = {param: value for param, value in config_dict.items() if param in config_fields}
        return cls(**override)


@dataclass
class WhitespaceConfig:
    space_count: int
    separator: str
    indent: str
    continuation_indent: str
    line_ending: str
    line_length: int


@dataclass
class RawLinterConfig:
    configure: list[str] | None = None
    select: list[str] | None = None
    extend_select: list[str] | None = None
    ignore: list[str] | None = None
    fixable: list[str] | None = None
    unfixable: list[str] | None = None
    per_file_ignores: dict[str, list[str]] | None = None
    issue_format: str | None = None
    threshold: RuleSeverity | None = None
    custom_rules: list[str] | None = None
    reports: list[str] | None = None
    persistent: bool | None = None
    compare: bool | None = None
    exit_zero: bool | None = None
    fix: bool | None = None
    unsafe_fixes: bool | None = None
    diff: bool | None = None
    return_result: bool | None = None
    silent: bool | None = None

    @classmethod
    def from_dict(cls, config_dict: dict[str, Any], config_path: Path, silent: bool | None) -> RawLinterConfig:
        config_fields = {config_field.name for config_field in fields(cls)}
        validate_config_fields(config_dict=config_dict, known_fields=config_fields, config_path=config_path)
        if "threshold" in config_dict:
            config_dict["threshold"] = parse_rule_severity(config_dict["threshold"])
        if "custom_rules" in config_dict:
            config_dict["custom_rules"] = [
                resolve_relative_path(path, config_path.parent, ensure_exists=True)
                for path in config_dict["custom_rules"]
            ]
        return cls(**config_dict, silent=silent)


@dataclass
class LinterConfig:
    select: list[str]
    extend_select: list[str]
    ignore: list[str]
    fixable: list[str]
    unfixable: list[str]
    custom_rules: list[str]
    configure: list[str]
    per_file_ignores: dict[str, list[str]]
    issue_format: str
    target_version: Version
    threshold: RuleSeverity
    reports: list[str]
    persistent: bool
    compare: bool
    exit_zero: bool
    fix: bool
    unsafe_fixes: bool
    diff: bool
    return_result: bool
    silent: bool
    hash: int

    def __hash__(self) -> int:
        return self.hash


@dataclass
class RawSkipConfig:
    skip: set[str] | None = None
    sections: set[str] | None = None
    keyword_call: set[str] | None = None
    keyword_call_pattern: set[str] | None = None

    @classmethod
    def from_dict(cls, config_dict: dict[str, list[str]]) -> RawSkipConfig:
        override = {
            "skip": set(config_dict["skip"]) if "skip" in config_dict else None,
            "sections": set(config_dict["skip_sections"]) if "skip_sections" in config_dict else None,
            "keyword_call": set(config_dict["skip_keyword_call"]) if "skip_keyword_call" in config_dict else None,
            "keyword_call_pattern": set(config_dict["skip_keyword_call_pattern"])
            if "skip_keyword_call_pattern" in config_dict
            else None,
        }
        return cls(**override)


@dataclass
class SkipConfig:
    skip: set[str]
    sections: set[str]
    keyword_call: set[str]
    keyword_call_pattern: set[str]

    @property
    def config_fields(self) -> set[str]:
        return {"skip", "skip_sections", "skip_keyword_call", "skip_keyword_call_pattern"}

    def update_with_str_config(self, **kwargs: str) -> None:
        for name, value in kwargs.items():
            if name == "keyword_call":
                self.keyword_call.update(value.split(","))
            elif name == "keyword_call_pattern":
                self.keyword_call_pattern.update(value.split(","))
            elif name == "sections":
                self.sections.update(value.split(","))
            elif value.lower() == "true":
                self.skip.add(name)
            else:
                self.skip.discard(name)


@dataclass
class RawFormatterConfig:
    whitespace_config: RawWhitespaceConfig | None = None
    skip_config: RawSkipConfig | None = None
    select: list[str] | None = None
    extend_select: list[str] | None = None
    configure: list[str] | None = None
    force_order: bool | None = None
    allow_disabled: bool | None = None
    overwrite: bool | None = None
    diff: bool | None = None
    output: Path | None = None
    color: bool | None = None
    check: bool | None = None
    reruns: int | None = None
    start_line: int | None = None
    end_line: int | None = None
    return_result: bool | None = None

    @classmethod
    def from_dict(cls, config_dict: dict[str, Any], config_parent: Path) -> RawFormatterConfig:
        config_fields = {config_field.name for config_field in fields(cls)}
        known_fields = (
            config_fields
            | {config_field.name for config_field in fields(RawWhitespaceConfig)}
            | {
                (f"skip_{config_field.name}" if not config_field.name.startswith("skip") else config_field.name)
                for config_field in fields(RawSkipConfig)
            }
        )
        if unknown_fields := {param: value for param, value in config_dict.items() if param not in known_fields}:
            print(f"Unknown fields in the [robocop.format] section: {unknown_fields}")
            raise typer.Exit(code=1)
        override = {param: value for param, value in config_dict.items() if param in config_fields}
        override["whitespace_config"] = RawWhitespaceConfig.from_dict(config_dict)
        override["skip_config"] = RawSkipConfig.from_dict(config_dict)
        for param in ("select", "extend_select"):
            if param in override:
                override[param] = [
                    resolve_relative_path(path, config_parent, ensure_exists=True) for path in config_dict[param]
                ]

        return cls(**override)


@dataclass
class FormatterConfig:
    select: list[str]
    extend_select: list[str]
    configure: list[str]
    force_order: bool
    allow_disabled: bool
    target_version: Version
    skip_config: SkipConfig
    languages: Languages | None
    whitespace_config: WhitespaceConfig
    diff: bool
    color: bool
    check: bool
    overwrite: bool
    reruns: int
    start_line: int | None
    end_line: int | None
    output: Path | None
    silent: bool
    return_result: bool
    hash: int

    def __hash__(self) -> int:
        return self.hash

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FormatterConfig):
            raise NotImplementedError
        return (
            self.hash == other.hash
            and self.force_order == other.force_order
            and self.skip_config == other.skip_config
            and self.whitespace_config == other.whitespace_config
            and self.diff == other.diff
            and self.color == other.color
            and self.check == other.check
            and self.overwrite == other.overwrite
            and self.reruns == other.reruns
            and self.start_line == other.start_line
            and self.end_line == other.end_line
            and self.silent == other.silent
            and self.return_result == other.return_result
        )


@dataclass
class RawCacheConfig:
    enabled: bool | None = None
    cache_dir: Path | None = None

    @classmethod
    def from_dict(cls, config: dict[str, Any], config_parent: Path) -> RawCacheConfig:
        enabled = config.pop("cache", True)
        cache_dir = config.pop("cache_dir", None)
        if cache_dir is not None:
            cache_dir = Path(cache_dir)
            if not cache_dir.is_absolute():
                cache_dir = config_parent / cache_dir
        return cls(enabled=enabled, cache_dir=cache_dir)


@dataclass
class CacheConfig:
    """Configuration for file-level caching."""

    enabled: bool
    cache_dir: Path


@dataclass
class RawFileFiltersOptions:
    include: list[str] | None = None
    default_include: list[str] | None = None
    exclude: list[str] | None = None
    default_exclude: list[str] | None = None

    @classmethod
    def from_dict(cls, config: dict[str, Any]) -> RawFileFiltersOptions:
        allowed = ["include", "exclude", "default_include", "default_exclude"]
        filter_config = {key: config.pop(key, None) for key in allowed}
        return cls(**filter_config)


@dataclass
class FileFiltersOptions:
    included_paths: set[str]
    excluded_paths: set[str]

    def path_excluded(self, path: Path) -> bool:
        """Exclude all paths matching exclude patterns."""
        return any(path.match(pattern) for pattern in self.excluded_paths)

    def path_included(self, path: Path) -> bool:
        """Only allow paths matching include patterns."""
        return any(path.match(pattern) for pattern in self.included_paths)


@dataclass
class RawConfig:
    sources: list[str] | None = None
    file_filters: RawFileFiltersOptions | None = None
    linter: RawLinterConfig | None = None
    formatter: RawFormatterConfig | None = None
    cache: RawCacheConfig | None = None
    language: list[str] | None = None
    verbose: bool | None = None
    silent: bool | None = None
    target_version: TargetVersion | None = None
    config_source: str | None = None

    @classmethod
    def from_dict(cls, config_dict: dict[str, Any], config_path: Path) -> RawConfig:
        # TODO: how target version is handled for RawConfig??
        config_dict = normalize_config_keys(config_dict)
        validate_old_config(config_dict=config_dict, config_path=config_path)
        config_fields = {"sources", "cache", "cache_dir", "language", "verbose", "silent", "target_version"}
        known_fields = config_fields | {"lint", "format", "extends", "skip_gitignore"}
        known_fields.update({config_field.name for config_field in fields(RawFileFiltersOptions)})
        validate_config_fields(config_dict=config_dict, known_fields=known_fields, config_path=config_path)
        raw_dict = {param: value for param, value in config_dict.items() if param in config_fields}
        if "lint" in config_dict:
            raw_dict["linter"] = RawLinterConfig.from_dict(
                config_dict["lint"], config_path, silent=raw_dict.get("silent")
            )
        else:
            raw_dict["linter"] = None
        if "format" in config_dict:
            raw_dict["formatter"] = RawFormatterConfig.from_dict(config_dict["format"], config_path.parent)
        else:
            raw_dict["formatter"] = None
        if "target_version" in raw_dict:
            raw_dict["target_version"] = TargetVersion.from_string(str(raw_dict["target_version"]))
        raw_dict["cache"] = RawCacheConfig.from_dict(raw_dict, config_path.parent)
        raw_dict["file_filters"] = RawFileFiltersOptions.from_dict(config_dict)
        raw_dict["config_source"] = str(config_path)
        return cls(**raw_dict)


@dataclass(frozen=True)
class Config:
    sources: list[str]
    file_filters: FileFiltersOptions
    linter: LinterConfig
    formatter: FormatterConfig
    cache: CacheConfig
    languages: Languages | None
    verbose: bool
    silent: bool
    target_version: Version
    config_source: str
    hash: str

    def __str__(self) -> str:
        return str(self.config_source)

    def __hash__(self) -> int:
        return hash(self.hash)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Config):
            raise NotImplementedError
        return (
            self.hash == other.hash
            and self.sources == other.sources
            and self.file_filters == other.file_filters
            and self.linter == other.linter
            and self.formatter == other.formatter
            and self.cache.enabled == other.cache.enabled
            and self.verbose == other.verbose
            and self.silent == other.silent
            and self.target_version == other.target_version
        )
