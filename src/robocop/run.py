import textwrap
from pathlib import Path
from typing import Annotated, Any

import click
import typer
from rich.console import Console

from robocop import __version__, config
from robocop.config import defaults
from robocop.config.parser import compile_rule_pattern
from robocop.formatter.runner import RobocopFormatter
from robocop.linter import rules_list
from robocop.linter.diagnostics import Diagnostic
from robocop.linter.reports import load_reports, print_reports
from robocop.linter.rules import Rule, RuleSeverity
from robocop.linter.runner import RobocopLinter
from robocop.linter.utils.misc import ROBOCOP_RULES_URL, get_plural_form  # TODO: move higher up
from robocop.migrate_config import migrate_deprecated_configs
from robocop.runtime.resolver import ConfigResolver


class CliWithVersion(typer.core.TyperGroup):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        click.version_option(version=__version__)(self)

    def list_commands(self, ctx: click.Context) -> list[str]:  # noqa: ARG002
        """Return the list of commands in the set order."""
        commands = ["check", "check-project", "format", "list", "docs"]
        for command in self.commands:
            if command not in commands:
                commands.append(command)
        return commands


app = typer.Typer(
    name="robocop",
    help="Static code analysis tool (linter) and code formatter for Robot Framework. "
    "Full documentation available at https://robocop.dev.",
    context_settings={"help_option_names": ["-h", "--help"]},
    rich_markup_mode="rich",
    cls=CliWithVersion,
)
list_app = typer.Typer(help="List available rules, reports or formatters.")
app.add_typer(list_app, name="list")


config_option = Annotated[
    Path | None,
    typer.Option(
        "--config",
        help="Path to configuration file. It will overridden any configuration file found in the project.",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
        show_default=False,
        rich_help_panel="Configuration",
    ),
]
project_root_option = Annotated[
    Path | None,
    typer.Option(
        help="Project root directory. It is used to find default configuration directory",
        show_default="Automatically found from the sources and current working directory.",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        resolve_path=True,
        rich_help_panel="Other",
    ),
]
sources_argument = Annotated[
    list[Path] | None,
    typer.Argument(
        help="List of paths to be parsed by Robocop", show_default="current directory", rich_help_panel="File discovery"
    ),
]
include_option = Annotated[
    list[str] | None,
    typer.Option("--include", help="Include additional paths", show_default=False, rich_help_panel="File discovery"),
]
default_include_option = Annotated[
    list[str] | None,
    typer.Option(
        "--default-include",
        help="Override to change default includes",
        show_default=str(defaults.DEFAULT_INCLUDE),
        rich_help_panel="File discovery",
    ),
]
exclude_option = Annotated[
    list[str] | None,
    typer.Option(
        "--exclude", "-e", help="Exclude additional paths", show_default=False, rich_help_panel="File discovery"
    ),
]
default_exclude_option = Annotated[
    list[str] | None,
    typer.Option(
        "--default-exclude",
        help="Override to change default excludes",
        show_default=str(defaults.DEFAULT_EXCLUDE),
        rich_help_panel="File discovery",
    ),
]
force_exclude_option = Annotated[
    bool,
    typer.Option(
        "--force-exclude",
        help="Enforce exclusions, even for paths passed directly in the command-line.",
        show_default=False,
        rich_help_panel="File discovery",
    ),
]
language_option = Annotated[
    list[str] | None,
    typer.Option(
        "--language",
        "--lang",
        show_default="en",
        metavar="LANG",
        help="Parse Robot Framework files using additional languages.",
        rich_help_panel="Other",
    ),
]
verbose_option = Annotated[
    bool | None,
    typer.Option(
        help="More verbose output.",
        rich_help_panel="Other",
    ),
]
silent_option = Annotated[
    bool | None, typer.Option(help="Disable all logging.", show_default="--no-silent", rich_help_panel="Other")
]
ignore_git_dir_option = Annotated[
    bool,
    typer.Option(
        rich_help_panel="Configuration", help="Do not stop searching for config file when .git directory is found."
    ),
]
ignore_file_config_option = Annotated[
    bool, typer.Option(rich_help_panel="Configuration", help="Do not load configuration files.")
]
cache_option = Annotated[
    bool | None,
    typer.Option(
        "--cache/--no-cache",
        help="Disable file caching. All files will be processed regardless of modifications.",
        rich_help_panel="Caching",
    ),
]
clear_cache_option = Annotated[
    bool,
    typer.Option(
        "--clear-cache",
        help="Clear the cache before running. Use this to force reprocessing of all files.",
        rich_help_panel="Caching",
    ),
]
cache_dir_option = Annotated[
    Path | None,
    typer.Option(
        "--cache-dir",
        help="Directory to store cache files.",
        show_default=".robocop_cache in current directory",
        file_okay=False,
        dir_okay=True,
        rich_help_panel="Caching",
    ),
]
select_rules_option = Annotated[
    list[str] | None,
    typer.Option("--select", "-s", help="Select rules to run", show_default=False, rich_help_panel="Selecting rules"),
]
extend_select_rules_option = Annotated[
    list[str] | None,
    typer.Option(
        show_default=False,
        help="Select additional rules to run.",
        rich_help_panel="Selecting rules",
    ),
]
ignore_rules_option = Annotated[
    list[str] | None,
    typer.Option("--ignore", "-i", help="Ignore rules", show_default=False, rich_help_panel="Selecting rules"),
]
fixable_rules_option = Annotated[
    list[str] | None,
    typer.Option("--fixable", help="Select rules to fix", show_default=False, rich_help_panel="Selecting rules"),
]
unfixable_rules_option = Annotated[
    list[str] | None,
    typer.Option(
        "--unfixable",
        help="Select rules that should not be fixed",
        show_default=False,
        rich_help_panel="Selecting rules",
    ),
]
linter_target_version_option = Annotated[
    config.parser.TargetVersion | None,
    typer.Option(
        case_sensitive=False,
        help="Enable only rules supported by configured version",
        rich_help_panel="Selecting rules",
    ),
]
formatter_target_version = Annotated[
    config.parser.TargetVersion | None,
    typer.Option(
        case_sensitive=False,
        help="Enable only formatters supported by configured version",
        rich_help_panel="Selecting formatters",
    ),
]
linter_threshold_option = Annotated[
    RuleSeverity | None,
    typer.Option(
        "--threshold",
        "-t",
        help="Disable rules below given threshold",
        show_default=RuleSeverity.INFO.value,
        parser=config.parser.parse_rule_severity,
        metavar="I/W/E",
        rich_help_panel="Selecting rules",
    ),
]
linter_configure_option = Annotated[
    list[str] | None,
    typer.Option(
        "--configure",
        "-c",
        help="Configure checker or report with parameter value",
        metavar="rule.param=value",
        show_default=False,
        rich_help_panel="Configuration",
    ),
]
reports_option = Annotated[
    list[str] | None,
    typer.Option(
        "--reports",
        "-r",
        show_default=False,
        help="Generate reports from reported issues. To list available reports use `list reports` command. "
        "Use `all` to enable all reports.",
        rich_help_panel="Reports",
    ),
]
fix_option = Annotated[bool | None, typer.Option(help="Fix lint violations", rich_help_panel="Fix")]
unsafe_fixes_option = Annotated[bool | None, typer.Option(help="Apply potentially unsafe fixes", rich_help_panel="Fix")]
diff_option = Annotated[
    bool | None,
    typer.Option(help="Show diff of fixes without modifying files. Implies --fix", rich_help_panel="Fix"),
]
separator_help = """
Token separator to use in the outputs:

- [bold]space[/bold]:   use --space-count spaces to separate tokens

- tab:     use a single tabulation to separate tokens
"""
line_ending_help = """
Line separator to use in the outputs:

    - [bold]native[/bold]:  use operating system's native line endings

    - windows: use Windows line endings (CRLF)

    - unix:    use Unix line endings (LF)

    - auto:    maintain existing line endings (uses what's used in the first line)
"""


@app.command(name="check")
def check_files(
    sources: sources_argument = None,
    select: select_rules_option = None,
    extend_select: extend_select_rules_option = None,
    ignore: ignore_rules_option = None,
    fixable: fixable_rules_option = None,
    unfixable: unfixable_rules_option = None,
    target_version: linter_target_version_option = None,
    threshold: linter_threshold_option = None,
    include: include_option = None,
    default_include: default_include_option = None,
    exclude: exclude_option = None,
    default_exclude: default_exclude_option = None,
    force_exclude: force_exclude_option = False,
    fix: fix_option = None,
    unsafe_fixes: unsafe_fixes_option = None,
    diff: diff_option = False,  # cannot be overridden from the config
    configuration_file: config_option = None,
    configure: linter_configure_option = None,
    reports: reports_option = None,
    issue_format: Annotated[
        str | None,
        typer.Option("--issue-format", show_default=defaults.DEFAULT_ISSUE_FORMAT, rich_help_panel="Other"),
    ] = None,
    language: language_option = None,
    custom_rules: Annotated[
        list[str] | None,
        typer.Option("--custom-rules", help="Load custom rules", show_default=False, rich_help_panel="Selecting rules"),
    ] = None,
    ignore_git_dir: ignore_git_dir_option = False,
    ignore_file_config: ignore_file_config_option = False,
    skip_gitignore: Annotated[
        bool, typer.Option(help="Do not skip files listed in .gitignore files", rich_help_panel="File discovery")
    ] = False,
    persistent: Annotated[
        bool | None,
        typer.Option(
            help="Use this flag to save Robocop reports in cache directory for later comparison.",
            rich_help_panel="Reports",
        ),
    ] = None,
    compare: Annotated[
        bool | None,
        typer.Option(
            help="Compare reports results with previous results (saved with --persistent)", rich_help_panel="Reports"
        ),
    ] = None,
    gitlab: Annotated[
        bool,
        typer.Option(
            help="Generate Gitlab Code Quality report. Equivalent of --reports gitlab",
            rich_help_panel="Reports",
        ),
    ] = False,
    exit_zero: Annotated[
        bool | None,
        typer.Option(
            help="Always exit with 0 unless Robocop terminates abnormally.",
            show_default="--no-exit-zero",
            rich_help_panel="Other",
        ),
    ] = None,
    return_result: Annotated[
        bool,
        typer.Option(
            help="Return check results as list of Diagnostic messages instead of exiting from the application.",
            hidden=True,
        ),
    ] = False,
    root: project_root_option = None,
    verbose: verbose_option = None,
    silent: silent_option = None,
    cache: cache_option = None,
    clear_cache: clear_cache_option = False,
    cache_dir: cache_dir_option = None,
) -> list[Diagnostic]:
    """Lint Robot Framework files."""
    if gitlab:
        if not reports:
            reports = []
        reports.append("gitlab")
    file_filters = config.schema.RawFileFiltersOptions(
        include=include, default_include=default_include, exclude=exclude, default_exclude=default_exclude
    )
    linter_config = config.schema.RawLinterConfig(
        configure=configure,
        select=select,
        extend_select=extend_select,
        ignore=ignore,
        fixable=fixable,
        unfixable=unfixable,
        issue_format=issue_format,
        threshold=threshold,
        custom_rules=custom_rules,
        reports=reports,
        persistent=persistent,
        compare=compare,
        exit_zero=exit_zero,
        return_result=return_result,
        fix=fix,
        unsafe_fixes=unsafe_fixes,
        diff=diff,
    )
    cache_config = config.schema.RawCacheConfig(enabled=cache, cache_dir=cache_dir)
    overwrite_config = config.schema.RawConfig(
        linter=linter_config,
        formatter=None,
        file_filters=file_filters,
        cache=cache_config,
        language=language,
        silent=silent,
        verbose=verbose,
        target_version=target_version,
    )
    manager = config.manager.ConfigManager(
        sources=sources,
        config=configuration_file,
        root=root,
        ignore_git_dir=ignore_git_dir,
        ignore_file_config=ignore_file_config,
        skip_gitignore=skip_gitignore,
        force_exclude=force_exclude,
        overwrite_config=overwrite_config,
    )
    if clear_cache:
        manager.cache.invalidate_all()
    runner = RobocopLinter(manager)
    return runner.run()


@app.command(name="check-project")
def check_project(
    sources: sources_argument = None,
    select: select_rules_option = None,
    extend_select: extend_select_rules_option = None,
    ignore: ignore_rules_option = None,
    target_version: linter_target_version_option = None,
    threshold: linter_threshold_option = None,
    include: include_option = None,
    default_include: default_include_option = None,
    exclude: exclude_option = None,
    default_exclude: default_exclude_option = None,
    force_exclude: force_exclude_option = False,
    configuration_file: config_option = None,
    configure: linter_configure_option = None,
    reports: reports_option = None,
    issue_format: Annotated[
        str | None,
        typer.Option("--issue-format", show_default=defaults.DEFAULT_ISSUE_FORMAT, rich_help_panel="Other"),
    ] = None,
    language: language_option = None,
    custom_rules: Annotated[
        list[str] | None,
        typer.Option("--custom-rules", help="Load custom rules", show_default=False, rich_help_panel="Selecting rules"),
    ] = None,
    ignore_git_dir: ignore_git_dir_option = False,
    ignore_file_config: ignore_file_config_option = False,
    skip_gitignore: Annotated[
        bool | None, typer.Option(help="Do not skip files listed in .gitignore files", rich_help_panel="File discovery")
    ] = False,
    persistent: Annotated[
        bool | None,
        typer.Option(
            help="Use this flag to save Robocop reports in cache directory for later comparison.",
            rich_help_panel="Reports",
        ),
    ] = None,
    compare: Annotated[
        bool | None,
        typer.Option(
            help="Compare reports results with previous results (saved with --persistent)", rich_help_panel="Reports"
        ),
    ] = None,
    gitlab: Annotated[
        bool | None,
        typer.Option(
            help="Generate Gitlab Code Quality report. Equivalent of --reports gitlab",
            rich_help_panel="Reports",
        ),
    ] = False,
    exit_zero: Annotated[
        bool | None,
        typer.Option(
            help="Always exit with 0 unless Robocop terminates abnormally.",
            show_default="--no-exit-zero",
            rich_help_panel="Other",
        ),
    ] = None,
    return_result: Annotated[
        bool,
        typer.Option(
            help="Return check results as list of Diagnostic messages instead of exiting from the application.",
            hidden=True,
        ),
    ] = False,
    root: project_root_option = None,
    verbose: verbose_option = None,
    silent: silent_option = None,
) -> list[Diagnostic]:
    """Analyse the whole project using project level checkers."""
    if gitlab:
        if not reports:
            reports = []
        reports.append("gitlab")
    linter_config = config.schema.RawLinterConfig(
        configure=configure,
        select=select,
        extend_select=extend_select,
        ignore=ignore,
        issue_format=issue_format,
        threshold=threshold,
        custom_rules=custom_rules,
        reports=reports,
        persistent=persistent,
        compare=compare,
        exit_zero=exit_zero,
        return_result=return_result,
    )
    file_filters = config.schema.RawFileFiltersOptions(
        include=include, default_include=default_include, exclude=exclude, default_exclude=default_exclude
    )
    overwrite_config = config.schema.RawConfig(
        linter=linter_config,
        formatter=None,
        file_filters=file_filters,
        language=language,
        verbose=verbose,
        silent=silent,
        target_version=target_version,
    )
    manager = config.manager.ConfigManager(
        sources=sources,
        config=configuration_file,
        root=root,
        ignore_git_dir=ignore_git_dir,
        ignore_file_config=ignore_file_config,
        skip_gitignore=skip_gitignore,
        force_exclude=force_exclude,
        overwrite_config=overwrite_config,
    )
    runner = RobocopLinter(manager)
    return runner.run_project_checks()


@app.command(name="format")
def format_files(
    sources: sources_argument = None,
    select: Annotated[
        list[str] | None,
        typer.Option(
            show_default=False,
            metavar="FORMATTER",
            help="Select formatters to run.",
            rich_help_panel="Selecting formatters",
        ),
    ] = None,
    extend_select: Annotated[
        list[str] | None,
        typer.Option(
            show_default=False,
            metavar="FORMATTER",
            help="Select additional formatters to run.",
            rich_help_panel="Selecting formatters",
        ),
    ] = None,
    force_order: Annotated[
        bool | None,
        typer.Option(help="Use formatters in a order as provided in the cli", rich_help_panel="Selecting formatters"),
    ] = None,
    include: include_option = None,
    default_include: default_include_option = None,
    exclude: exclude_option = None,
    default_exclude: default_exclude_option = None,
    force_exclude: force_exclude_option = False,
    configure: Annotated[
        list[str] | None,
        typer.Option(
            "--configure",
            "-c",
            help="Configure checker or report with parameter value",
            metavar="rule.param=value",
            show_default=False,
            rich_help_panel="Configuration",
        ),
    ] = None,
    configuration_file: config_option = None,
    overwrite: Annotated[
        bool | None, typer.Option(help="Write changes back to file", rich_help_panel="Work modes")
    ] = None,
    diff: Annotated[
        bool | None, typer.Option(help="Show difference after formatting the file", rich_help_panel="Work modes")
    ] = None,
    color: Annotated[
        bool | None, typer.Option(help="Colorized difference", show_default="--color", rich_help_panel="Work modes")
    ] = None,
    check: Annotated[
        bool | None,
        typer.Option(
            help="Do not overwrite files, and exit with return status depending on if any file would be modified",
            rich_help_panel="Work modes",
        ),
    ] = None,
    space_count: Annotated[
        int | None,
        typer.Option(show_default="4", help="Number of spaces between cells", rich_help_panel="Formatting settings"),
    ] = None,
    indent: Annotated[
        int | None,
        typer.Option(
            show_default="same as --space-count",
            help="The number of spaces to be used as indentation",
            rich_help_panel="Formatting settings",
        ),
    ] = None,
    continuation_indent: Annotated[
        int | None,
        typer.Option(
            show_default="same as --space-count",
            help="The number of spaces to be used as separator after ... (line continuation) token",
            rich_help_panel="Formatting settings",
        ),
    ] = None,
    line_length: Annotated[
        int | None,
        typer.Option(show_default="120", help="Number of spaces between cells", rich_help_panel="Formatting settings"),
    ] = None,
    separator: Annotated[
        str | None, typer.Option(show_default="space", help=separator_help, rich_help_panel="Formatting settings")
    ] = None,
    line_ending: Annotated[
        str | None, typer.Option(show_default="native", help=line_ending_help, rich_help_panel="Formatting settings")
    ] = None,
    start_line: Annotated[
        int | None,
        typer.Option(
            show_default=False,
            help="Limit formatting only to selected area. "
            "If --end-line is not provided, format text only at --start-line",
            rich_help_panel="Formatting settings",
        ),
    ] = None,
    end_line: Annotated[
        int | None,
        typer.Option(
            show_default=False, help="Limit formatting only to selected area.", rich_help_panel="Formatting settings"
        ),
    ] = None,
    target_version: formatter_target_version = None,
    skip: Annotated[
        list[str] | None,
        typer.Option(
            show_default=False,
            help="Skip formatting of code block with the given type",
            rich_help_panel="Skip formatting",
        ),
    ] = None,
    skip_sections: Annotated[
        list[str] | None,
        typer.Option(
            show_default=False, help="Skip formatting of selected sections", rich_help_panel="Skip formatting"
        ),
    ] = None,
    skip_keyword_call: Annotated[
        list[str] | None,
        typer.Option(
            show_default=False,
            help="Skip formatting of keywords with the given name",
            rich_help_panel="Skip formatting",
        ),
    ] = None,
    skip_keyword_call_pattern: Annotated[
        list[str] | None,
        typer.Option(
            show_default=False,
            help="Skip formatting of keywords that matches with the given pattern",
            rich_help_panel="Skip formatting",
        ),
    ] = None,
    ignore_git_dir: ignore_git_dir_option = False,
    ignore_file_config: ignore_file_config_option = False,
    skip_gitignore: Annotated[bool, typer.Option(rich_help_panel="File discovery")] = False,
    reruns: Annotated[
        int | None,
        typer.Option(
            "--reruns",
            "-r",
            help="Rerun formatting up to reruns times until the code stops changing.",
            show_default="0",
            rich_help_panel="Work modes",
        ),
    ] = None,
    output: Annotated[Path | None, typer.Option(rich_help_panel="Other")] = None,
    language: language_option = None,
    root: project_root_option = None,
    verbose: verbose_option = None,
    silent: silent_option = None,
    cache: cache_option = None,
    clear_cache: clear_cache_option = False,
    cache_dir: cache_dir_option = None,
    return_result: Annotated[
        bool,
        typer.Option(
            help="Do not exit from the application and return exit code instead.",
            hidden=True,
        ),
    ] = False,
) -> int:
    """Format Robot Framework files."""
    whitespace_config = config.schema.RawWhitespaceConfig(
        space_count=space_count,
        indent=indent,
        continuation_indent=continuation_indent,
        line_ending=line_ending,
        separator=separator,
        line_length=line_length,
    )
    skip_config = config.schema.RawSkipConfig(
        skip=set(skip) if skip else None,
        keyword_call=set(skip_keyword_call) if skip_keyword_call else None,
        keyword_call_pattern=set(skip_keyword_call_pattern) if skip_keyword_call_pattern else None,
        sections=set(skip_sections) if skip_sections else None,
    )
    formatter_config = config.schema.RawFormatterConfig(
        select=select,
        extend_select=extend_select,
        force_order=force_order,
        whitespace_config=whitespace_config,
        skip_config=skip_config,
        configure=configure,
        overwrite=overwrite,
        output=output,
        diff=diff,
        color=color,
        check=check,
        start_line=start_line,
        end_line=end_line,
        reruns=reruns,
        return_result=return_result,
    )
    file_filters = config.schema.RawFileFiltersOptions(
        include=include, default_include=default_include, exclude=exclude, default_exclude=default_exclude
    )
    cache_config = config.schema.RawCacheConfig(enabled=cache, cache_dir=cache_dir)
    overwrite_config = config.schema.RawConfig(
        formatter=formatter_config,
        language=language,
        file_filters=file_filters,
        cache=cache_config,
        verbose=verbose,
        silent=silent,
        target_version=target_version,
    )
    manager = config.manager.ConfigManager(
        sources=sources,
        config=configuration_file,
        root=root,
        ignore_git_dir=ignore_git_dir,
        ignore_file_config=ignore_file_config,
        skip_gitignore=skip_gitignore,
        force_exclude=force_exclude,
        overwrite_config=overwrite_config,
    )
    if clear_cache:
        manager.cache.invalidate_all()
    runner = RobocopFormatter(manager)
    return runner.run()


@list_app.command(name="rules")
def list_rules(
    filter_category: Annotated[
        rules_list.RuleFilter, typer.Option("--filter", case_sensitive=False, help="Filter rules by category.")
    ] = rules_list.RuleFilter.ALL,
    filter_pattern: Annotated[str | None, typer.Option("--pattern", help="Filter rules by pattern")] = None,
    target_version: linter_target_version_option = None,
    with_fix: Annotated[bool, typer.Option("--with-fix", help="Show only fixable rules")] = False,
    silent: silent_option = None,
    return_result: Annotated[
        bool,
        typer.Option(
            help="Return list of available rules instead of exiting from the application.",
            hidden=True,
        ),
    ] = False,
) -> list[Rule] | None:
    """
    List available rules.

    Use the ` -- filter `` option to list only selected rules:

    > robocop list rules --filter DISABLED

    You can also specify the patterns to filter by:

    > robocop list rules --pattern *var*

    Use `robocop rule rule_name` for more detailed information on the rule.
    The output list is affected by a default configuration file (if it is found).
    """
    # TODO: rich support (colorized enabled, severity etc)
    console = Console(soft_wrap=True)
    overwrite_config = config.schema.RawConfig(
        silent=silent,
        target_version=target_version,
    )
    manager = config.manager.ConfigManager(overwrite_config=overwrite_config)
    resolver = ConfigResolver(load_rules=True)
    resolved_config = resolver.resolve_config(manager.default_config)
    if filter_pattern:
        compiled_pattern = compile_rule_pattern(filter_pattern)
        rules = rules_list.filter_rules_by_pattern(resolved_config.rules, compiled_pattern)
    else:
        rules = rules_list.filter_rules_by_category(
            resolved_config.rules, filter_category, manager.default_config.linter.target_version
        )
    if with_fix:
        rules = rules_list.filter_rules_by_fixability(rules)
    severity_counter = {"E": 0, "W": 0, "I": 0}
    enabled = 0
    for rule in rules:
        rule.enabled = rule.enabled and not rule.is_disabled(manager.default_config.linter.target_version)
        enabled += int(rule.enabled)
        if not silent:
            console.print(rule.rule_short_description(manager.default_config.linter.target_version))
        severity_counter[rule.severity.value] += 1
    configurable_rules_sum = sum(severity_counter.values())
    plural = get_plural_form(configurable_rules_sum)
    if not silent:
        console.print(f"\nAltogether {configurable_rules_sum} rule{plural} ({enabled} enabled).\n")
        print(f"Visit {ROBOCOP_RULES_URL.format(version='stable')} page for detailed documentation.")
    if return_result:
        return rules
    return None


@list_app.command(name="reports")
def list_reports(
    enabled: Annotated[
        bool | None,
        typer.Option(
            "--enabled/--disabled",
            help="List enabled or disabled reports. Reports configuration will be loaded from the default "
            "configuration file or `--reports`` option.",
            show_default=False,
        ),
    ] = None,
    reports: Annotated[
        list[str] | None,
        typer.Option(
            "--reports",
            "-r",
            show_default=False,
            help="Enable selected reports.",
        ),
    ] = None,
    silent: silent_option = None,
) -> None:
    """List available reports."""
    console = Console(soft_wrap=True)
    linter_config = config.schema.RawLinterConfig(reports=reports)
    overwrite_config = config.schema.RawConfig(linter=linter_config, silent=silent)
    manager = config.manager.ConfigManager(overwrite_config=overwrite_config)
    runner = RobocopLinter(manager)
    if not silent:
        console.print(print_reports(runner.reports, enabled))  # TODO: color etc


@list_app.command(name="formatters")
def list_formatters(
    filter_category: Annotated[
        rules_list.RuleFilter, typer.Option("--filter", case_sensitive=False, help="Filter formatters by category.")
    ] = rules_list.RuleFilter.ALL,
    target_version: formatter_target_version = None,
    silent: silent_option = None,
) -> None:
    """List available formatters."""
    from rich.table import Table  # noqa: PLC0415

    console = Console(soft_wrap=True)
    overwrite_config = config.schema.RawConfig(
        silent=silent, target_version=target_version, formatter=config.schema.RawFormatterConfig(allow_disabled=True)
    )
    manager = config.manager.ConfigManager(overwrite_config=overwrite_config)
    resolver = ConfigResolver(load_rules=True, load_formatters=True)
    resolved_config = resolver.resolve_config(manager.default_config)

    if filter_category == filter_category.ALL:
        formatters = list(resolved_config.formatters.values())
    elif filter_category == filter_category.ENABLED:
        formatters = [formatter for formatter in resolved_config.formatters.values() if formatter.ENABLED]
    elif filter_category == filter_category.DISABLED:
        formatters = [formatter for formatter in resolved_config.formatters.values() if not formatter.ENABLED]
    else:
        raise ValueError(f"Unrecognized rule category '{filter_category}'")
    if not silent:
        table = Table(title="Formatters", header_style="bold red")
        table.add_column("Name", justify="left", no_wrap=True)
        table.add_column("Enabled")
        for formatter in formatters:
            decorated_enable = "Yes" if formatter.ENABLED else "No"
            table.add_row(formatter.__class__.__name__, decorated_enable)
        console.print(table)
        console.print(
            "To see detailed docs run:\n"
            "    [bold]robocop docs [blue]formatter_name[/][/]\n"
            "Non-default formatters needs to be selected explicitly with [bold cyan]--select[/] or "
            "configured with param `enabled=True`.\n"
        )


@app.command("docs")
def print_resource_documentation(name: Annotated[str, typer.Argument(help="Rule name")]) -> None:
    """Print formatter, rule or report documentation."""
    # TODO load external from cli
    console = Console(soft_wrap=True)
    manager = config.manager.ConfigManager()
    resolver = ConfigResolver(load_rules=True, load_formatters=True)
    resolved_config = resolver.resolve_config(manager.default_config)

    if name in resolved_config.rules:
        console.print(resolved_config.rules[name].description_with_configurables)
        return

    reports = load_reports(manager.default_config)
    if name in reports:
        docs = textwrap.dedent(str(reports[name].__doc__))
        console.print(docs)
        return

    if name in resolved_config.formatters:
        docs = textwrap.dedent(resolved_config.formatters[name].__doc__)
        console.print(f"Formatter [bold]{name}[/bold]:")
        console.print(docs)
        console.print(f"See https://robocop.dev/stable/formatter/formatters/{name}/ for more information.")
    else:
        console.print(f"There is no rule, formatter or a report with a '{name}' name.")
        raise typer.Exit(code=2)


@app.command("migrate")
def migrate_config(
    config_path: Annotated[
        Path, typer.Argument(help="Path to the configuration file to be migrated.", show_default=False)
    ],
) -> None:
    """
    Migrate Robocop and Robotidy old configuration files to the new format supported by the Robocop 6.0.

    All the comments and formatting are not preserved. Robocop will take the original file and create a new, with the
    suffix ``_migrated``. The original configuration file should have the ``[tool.robocop]`` or / and
    ``[tool.robotidy]`` section.
    If there are both sections, and they contain a common option (such as include/exclude paths), the option from
    ``tool.robocop`` a section will take precedence.

    Rule ids and names will be also migrated. Patterns (such as ``*docs*``) will be, however, ignored.

    If you have separate configuration files for Robocop and Robotidy, run the command twice and merge it manually.
    """
    migrate_deprecated_configs(config_path)


def main() -> None:
    app(windows_expand_args=False)
