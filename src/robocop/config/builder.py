from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, TypeVar

try:
    from robot.api import Languages  # RF 6.0
except ImportError:
    Languages = None

from robocop.config import defaults
from robocop.config.hash import config_hash, formatter_hash, linter_hash
from robocop.config.parser import load_languages, parse_target_version
from robocop.config.schema import (
    CacheConfig,
    Config,
    FileFiltersOptions,
    FormatterConfig,
    LinterConfig,
    RawCacheConfig,
    RawConfig,
    RawFileFiltersOptions,
    RawFormatterConfig,
    RawLinterConfig,
    RawSkipConfig,
    RawWhitespaceConfig,
    SkipConfig,
    WhitespaceConfig,
)
from robocop.linter.rules import RuleSeverity

if TYPE_CHECKING:
    from robocop.version_handling import Version

_T = TypeVar("_T")


def resolve(
    cli: object | None,
    file: object | None,
    attr: str,
    default: _T,
) -> _T:
    """
    Resolve the configuration value.

    The CLI config or configuration file can be not present.
    If it's present, the value itself can be unset (None).
    It should return the first non-None value in the given order
    (cli -> config file -> default).
    """
    if cli is not None:
        value: _T | None = getattr(cli, attr, None)
        if value is not None:
            return value

    if file is not None:
        value = getattr(file, attr, None)
        if value is not None:
            return value

    return default


def merge_lists(
    file: object | None,
    cli: object | None,
    attr: str,
) -> list:
    """
    Resolve and merge configuration values.

    Some configuration values like ``configure`` are not overwritten but joined together.
    """
    result = []
    if file is not None:
        value = getattr(file, attr, None)
        if value is not None:
            result.extend(value)
    if cli is not None:
        value = getattr(cli, attr, None)
        if value is not None:
            result.extend(value)
    return result


class ConfigBuilder:
    def from_raw(self, cli_raw: RawConfig | None, file_raw: RawConfig | None) -> Config:
        sources: list[str] = resolve(cli_raw, file_raw, "sources", ["."])
        language: list[str] = resolve(cli_raw, file_raw, "language", [])
        verbose = resolve(cli_raw, file_raw, "verbose", defaults.VERBOSE)
        silent = resolve(cli_raw, file_raw, "silent", defaults.SILENT)

        target_version = resolve(cli_raw, file_raw, "target_version", None)
        validated_version = parse_target_version(target_version)

        languages = load_languages(language)

        file_filters = self.file_filters_from_raw(
            cli_raw.file_filters if cli_raw else None,
            file_raw.file_filters if file_raw else None,
        )

        linter = self.linter_from_raw(
            cli_raw.linter if cli_raw else None, file_raw.linter if file_raw else None, validated_version, silent
        )

        formatter = self.formatter_from_raw(
            cli_raw.formatter if cli_raw else None,
            file_raw.formatter if file_raw else None,
            validated_version,
            languages,
            silent,
        )

        cache = self.cache_config_from_raw(
            cli_raw.cache if cli_raw else None,
            file_raw.cache if file_raw else None,
        )

        config_source = resolve(None, file_raw, "config_source", "cli")

        if config_source != "cli" and verbose and not silent:
            print(f"Loaded {config_source} configuration file.")

        hash_str = config_hash(linter.hash, formatter.hash, language)

        return Config(
            sources=sources,
            file_filters=file_filters,
            linter=linter,
            formatter=formatter,
            cache=cache,
            languages=languages,
            verbose=verbose,
            silent=silent,
            target_version=validated_version,
            config_source=config_source,
            hash=hash_str,
        )

    def linter_from_raw(
        self,
        cli_raw: RawLinterConfig | None,
        file_raw: RawLinterConfig | None,
        target_version: Version,
        silent: bool,
    ) -> LinterConfig:
        configure: list[str] = merge_lists(cli_raw, file_raw, "configure")
        select: list[str] = resolve(cli_raw, file_raw, "select", [])
        extend_select: list[str] = resolve(cli_raw, file_raw, "extend_select", [])
        ignore: list[str] = resolve(cli_raw, file_raw, "ignore", [])
        fixable: list[str] = resolve(cli_raw, file_raw, "fixable", [])
        unfixable: list[str] = resolve(cli_raw, file_raw, "unfixable", [])
        threshold: RuleSeverity = resolve(cli_raw, file_raw, "threshold", RuleSeverity.INFO)
        custom_rules: list[str] = resolve(cli_raw, file_raw, "custom_rules", [])
        per_file_ignores: dict[str, list[str]] = resolve(cli_raw, file_raw, "per_file_ignores", {})
        issue_format: str = resolve(cli_raw, file_raw, "issue_format", defaults.DEFAULT_ISSUE_FORMAT)
        reports: list[str] = merge_lists(cli_raw, file_raw, "reports")
        persistent = resolve(cli_raw, file_raw, "persistent", defaults.PERSISTENT)
        compare = resolve(cli_raw, file_raw, "compare", defaults.COMPARE)
        exit_zero = resolve(cli_raw, file_raw, "exit_zero", defaults.EXIT_ZERO)
        fix = resolve(cli_raw, file_raw, "fix", defaults.FIX)
        unsafe_fixes = resolve(cli_raw, file_raw, "unsafe_fixes", defaults.UNSAFE_FIXES)
        diff = resolve(cli_raw, file_raw, "diff", defaults.FIX_DIFF)
        return_result = resolve(cli_raw, file_raw, "return_result", defaults.LINTER_RETURN_RESULT)

        calculated_hash = linter_hash(
            select, extend_select, ignore, configure, custom_rules, threshold, target_version, per_file_ignores
        )

        return LinterConfig(
            select=select,
            extend_select=extend_select,
            ignore=ignore,
            fixable=fixable,
            unfixable=unfixable,
            custom_rules=custom_rules,
            target_version=target_version,
            threshold=threshold,
            configure=configure,
            per_file_ignores=per_file_ignores,
            issue_format=issue_format,
            reports=reports,
            persistent=persistent,
            compare=compare,
            exit_zero=exit_zero,
            fix=fix,
            unsafe_fixes=unsafe_fixes,
            diff=diff,
            return_result=return_result,
            silent=silent,
            hash=calculated_hash,
        )

    def formatter_from_raw(
        self,
        cli_raw: RawFormatterConfig | None,
        file_raw: RawFormatterConfig | None,
        target_version: Version,
        languages: Languages | None,
        silent: bool,
    ) -> FormatterConfig:
        select: list[str] = resolve(cli_raw, file_raw, "select", [])
        extend_select: list[str] = resolve(cli_raw, file_raw, "extend_select", [])
        configure: list[str] = merge_lists(cli_raw, file_raw, "configure")
        force_order = resolve(cli_raw, file_raw, "force_order", defaults.FORCE_ORDER)
        allow_disabled = resolve(cli_raw, file_raw, "allow_disabled", defaults.ALLOW_DISABLED)
        overwrite = resolve(cli_raw, file_raw, "overwrite", defaults.OVERWRITE)
        diff = resolve(cli_raw, file_raw, "diff", defaults.DIFF)
        color = resolve(cli_raw, file_raw, "color", defaults.COLOR)
        check = resolve(cli_raw, file_raw, "check", defaults.CHECK)
        reruns = resolve(cli_raw, file_raw, "reruns", defaults.RERUNS)
        start_line = resolve(cli_raw, file_raw, "start_line", defaults.START_LINE)
        end_line = resolve(cli_raw, file_raw, "end_line", defaults.END_LINE)
        return_result = resolve(cli_raw, file_raw, "return_result", defaults.FORMATTER_RETURN_RESULT)
        output = resolve(cli_raw, file_raw, "output", None)

        overwrite_files = overwrite if overwrite is not None else not check

        whitespace_config = self.whitespace_config_from_raw(
            cli_raw.whitespace_config if cli_raw else None,
            file_raw.whitespace_config if file_raw else None,
        )
        skip_config = self.skip_config_from_raw(
            cli_raw.skip_config if cli_raw else None, file_raw.skip_config if file_raw else None
        )

        calculated_hash = formatter_hash(select, extend_select, configure, target_version, whitespace_config)
        return FormatterConfig(
            select=select,
            extend_select=extend_select,
            configure=configure,
            force_order=force_order,
            allow_disabled=allow_disabled,
            target_version=target_version,
            skip_config=skip_config,
            languages=languages,
            whitespace_config=whitespace_config,
            diff=diff,
            color=color,
            check=check,
            overwrite=overwrite_files,
            reruns=reruns,
            start_line=start_line,
            end_line=end_line,
            output=output,
            silent=silent,
            return_result=return_result,
            hash=calculated_hash,
        )

    def whitespace_config_from_raw(
        self, cli_raw: RawWhitespaceConfig | None, file_raw: RawWhitespaceConfig | None
    ) -> WhitespaceConfig:
        space_count = resolve(cli_raw, file_raw, "space_count", 4)
        indent = resolve(cli_raw, file_raw, "indent", None)
        if indent is None:
            indent = space_count
        continuation_indent = resolve(cli_raw, file_raw, "continuation_indent", None)
        if continuation_indent is None:
            continuation_indent = space_count
        separator = resolve(cli_raw, file_raw, "separator", "space")
        line_ending = resolve(cli_raw, file_raw, "line_ending", "native")
        line_length = resolve(cli_raw, file_raw, "line_length", 120)
        if separator == "space":
            separator_str = " " * space_count
            indent_str = " " * indent
            continuation_indent_str = " " * continuation_indent
        else:  # tab
            separator_str = "\t"
            indent_str = "\t"
            continuation_indent_str = "\t"
        if line_ending == "native":
            line_ending = os.linesep
        elif line_ending == "windows":
            line_ending = "\r\n"
        elif line_ending == "unix":
            line_ending = "\n"
        else:
            line_ending = "auto"
        return WhitespaceConfig(
            space_count=space_count,
            separator=separator_str,
            indent=indent_str,
            continuation_indent=continuation_indent_str,
            line_ending=line_ending,
            line_length=line_length,
        )

    def skip_config_from_raw(self, cli_raw: RawSkipConfig | None, file_raw: RawSkipConfig | None) -> SkipConfig:
        skip: list[str] = resolve(cli_raw, file_raw, "skip", [])
        skip_sections: list[str] = resolve(cli_raw, file_raw, "sections", [])
        skip_keyword_call: list[str] = resolve(cli_raw, file_raw, "keyword_call", [])
        skip_keyword_call_pattern: list[str] = resolve(cli_raw, file_raw, "keyword_call_pattern", [])
        return SkipConfig(
            skip=set(skip),
            sections=set(skip_sections),
            keyword_call=set(skip_keyword_call),
            keyword_call_pattern=set(skip_keyword_call_pattern),
        )

    def cache_config_from_raw(self, cli_raw: RawCacheConfig | None, file_raw: RawCacheConfig | None) -> CacheConfig:
        enabled = resolve(cli_raw, file_raw, "enabled", default=True)
        cache_dir = resolve(cli_raw, file_raw, "cache_dir", Path.cwd() / defaults.CACHE_DIR_NAME)
        return CacheConfig(enabled=enabled, cache_dir=cache_dir)

    def file_filters_from_raw(
        self, cli_raw: RawFileFiltersOptions | None, file_raw: RawFileFiltersOptions | None
    ) -> FileFiltersOptions:
        default_include: list[str] = resolve(cli_raw, file_raw, "default_include", list(defaults.DEFAULT_INCLUDE))
        include: list[str] = resolve(cli_raw, file_raw, "include", [])
        default_exclude: list[str] = resolve(cli_raw, file_raw, "default_exclude", list(defaults.DEFAULT_EXCLUDE))
        exclude: list[str] = resolve(cli_raw, file_raw, "exclude", [])
        included_paths = set(default_include).union(set(include))
        excluded_paths = set(default_exclude).union(set(exclude))
        return FileFiltersOptions(included_paths=included_paths, excluded_paths=excluded_paths)
