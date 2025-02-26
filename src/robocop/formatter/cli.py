from __future__ import annotations

import sys
from pathlib import Path
from re import Pattern

try:
    import rich_click as click

    RICH_PRESENT = True
except ImportError:  # Fails on vendored-in LSP plugin
    import click

    RICH_PRESENT = False

from robotidy import app, decorators, exceptions, files, skip, version
from robotidy import config as config_module
from robotidy.config import RawConfig, csv_list_type, validate_target_version
from robotidy.rich_console import console
from robotidy.transformers import TransformConfigMap, TransformConfigParameter, load_transformers
from robotidy.utils import misc

CLI_OPTIONS_LIST = [
    {
        "name": "Run only selected transformers",
        "options": ["--transform"],
    },
    {
        "name": "Load custom transformers",
        "options": ["--load-transformers"],
    },
    {
        "name": "Work modes",
        "options": ["--overwrite", "--diff", "--check", "--force-order"],
    },
    {
        "name": "Documentation",
        "options": ["--list", "--desc"],
    },
    {
        "name": "Configuration",
        "options": ["--configure", "--config", "--ignore-git-dir", "--generate-config"],
    },
    {
        "name": "Global formatting settings",
        "options": [
            "--spacecount",
            "--indent",
            "--continuation-indent",
            "--line-length",
            "--lineseparator",
            "--separator",
            "--startline",
            "--endline",
        ],
    },
    {"name": "File exclusion", "options": ["--exclude", "--extend-exclude", "--skip-gitignore"]},
    skip.option_group,
    {
        "name": "Other",
        "options": [
            "--target-version",
            "--language",
            "--reruns",
            "--verbose",
            "--color",
            "--output",
            "--version",
            "--help",
        ],
    },
]

if RICH_PRESENT:
    click.rich_click.USE_RICH_MARKUP = True
    click.rich_click.USE_MARKDOWN = True
    click.rich_click.FORCE_TERMINAL = None  # workaround rich_click trying to force color in GitHub Actions
    click.rich_click.STYLE_OPTION = "bold sky_blue3"
    click.rich_click.STYLE_SWITCH = "bold sky_blue3"
    click.rich_click.STYLE_METAVAR = "bold white"
    click.rich_click.STYLE_OPTION_DEFAULT = "grey37"
    click.rich_click.STYLE_OPTIONS_PANEL_BORDER = "grey66"
    click.rich_click.STYLE_USAGE = "magenta"
    click.rich_click.OPTION_GROUPS = {
        "robotidy": CLI_OPTIONS_LIST,
        "python -m robotidy": CLI_OPTIONS_LIST,
    }


CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


def validate_regex_callback(ctx: click.Context, param: click.Parameter, value: str | None) -> Pattern | None:
    return misc.validate_regex(value)


def validate_target_version_callback(
    ctx: click.Context, param: click.Option | click.Parameter, value: str | None
) -> int | None:
    return validate_target_version(value)


def validate_list_optional_value(ctx: click.Context, param: click.Option | click.Parameter, value: str | None):
    if not value:
        return value
    allowed = ["all", "enabled", "disabled"]
    if value not in allowed:
        raise click.BadParameter(f"Not allowed value. Allowed values are: {', '.join(allowed)}")
    return value


def csv_list_type_callback(ctx: click.Context, param: click.Option | click.Parameter, value: str | None) -> list[str]:
    return csv_list_type(value)


def print_transformer_docs(transformer):
    from rich.markdown import Markdown

    md = Markdown(str(transformer), code_theme="native", inline_code_lexer="robotframework")
    console.print(md)


@decorators.optional_rich
def print_description(name: str, target_version: int):
    # TODO: --desc works only for default transformers, it should also print custom transformer desc
    transformers = load_transformers(TransformConfigMap([], [], []), allow_disabled=True, target_version=target_version)
    transformer_by_names = {transformer.name: transformer for transformer in transformers}
    if name == "all":
        for transformer in transformers:
            print_transformer_docs(transformer)
    elif name in transformer_by_names:
        print_transformer_docs(transformer_by_names[name])
    else:
        rec_finder = misc.RecommendationFinder()
        similar = rec_finder.find_similar(name, transformer_by_names.keys())
        click.echo(f"Transformer with the name '{name}' does not exist.{similar}", err=True)
        return 1
    return 0


def _load_external_transformers(transformers: list, transformers_config: TransformConfigMap, target_version: int):
    external = []
    transformers_names = {transformer.name for transformer in transformers}
    transformers_from_conf = load_transformers(transformers_config, target_version=target_version)
    for transformer in transformers_from_conf:
        if transformer.name not in transformers_names:
            external.append(transformer)
    return external


@decorators.optional_rich
def print_transformers_list(global_config: config_module.MainConfig):
    from rich.table import Table

    target_version = global_config.default.target_version
    list_transformers = global_config.default.list_transformers
    config = global_config.get_config_for_source(Path.cwd())
    table = Table(title="Transformers", header_style="bold red")
    table.add_column("Name", justify="left", no_wrap=True)
    table.add_column("Enabled")
    transformers = load_transformers(TransformConfigMap([], [], []), allow_disabled=True, target_version=target_version)
    transformers.extend(_load_external_transformers(transformers, config.transformers_config, target_version))

    for transformer in transformers:
        enabled = transformer.name in config.transformers_lookup
        if list_transformers != "all":
            filter_by = list_transformers == "enabled"
            if enabled != filter_by:
                continue
        decorated_enable = "Yes" if enabled else "No"
        if enabled != transformer.enabled_by_default:
            decorated_enable = f"[bold magenta]{decorated_enable}*"
        table.add_row(transformer.name, decorated_enable)
    console.print(table)
    console.print(
        "Transformers are listed in the order they are run by default. If the transformer was enabled/disabled by the "
        "configuration the status will be displayed with extra asterisk (*) and in the [magenta]different[/] color."
    )
    console.print(
        "To see detailed docs run:\n"
        "    [bold]robotidy --desc [blue]transformer_name[/][/]\n"
        "or\n"
        "    [bold]robotidy --desc [blue]all[/][/]\n\n"
        "Non-default transformers needs to be selected explicitly with [bold cyan]--transform[/] or "
        "configured with param `enabled=True`.\n"
    )


def generate_config(global_config: config_module.MainConfig):
    try:
        import tomli_w
    except ImportError:
        raise exceptions.MissingOptionalTomliWDependencyError()
    target_version = global_config.default.target_version
    config = global_config.default_loaded
    transformers = load_transformers(TransformConfigMap([], [], []), allow_disabled=True, target_version=target_version)
    transformers.extend(_load_external_transformers(transformers, config.transformers_config, target_version))

    toml_config = {
        "tool": {
            "robotidy": {
                "diff": global_config.default_loaded.show_diff,
                "overwrite": global_config.default_loaded.overwrite,
                "verbose": global_config.default_loaded.verbose,
                "separator": global_config.default.separator,
                "spacecount": global_config.default_loaded.formatting.space_count,
                "line_length": global_config.default.line_length,
                "lineseparator": global_config.default.lineseparator,
                "skip_gitignore": global_config.default.skip_gitignore,
                "ignore_git_dir": global_config.default.ignore_git_dir,
            }
        }
    }
    configure_transformers = [
        f"{transformer.name}:enabled={transformer.name in config.transformers_lookup}" for transformer in transformers
    ]
    toml_config["tool"]["robotidy"]["configure"] = configure_transformers

    with open(global_config.default.generate_config, "w") as fp:
        fp.write(tomli_w.dumps(toml_config))


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option(
    "--transform",
    "-t",
    type=TransformConfigParameter(),
    multiple=True,
    metavar="TRANSFORMER_NAME",
    help="Transform files from [PATH(S)] with given transformer",
)
@click.option(
    "--load-transformers",
    "--custom-transformers",
    "custom_transformers",
    type=TransformConfigParameter(),
    multiple=True,
    metavar="TRANSFORMER_NAME",
    help="Load custom transformer from the path and run them after default ones.",
)
@click.option(
    "--configure",
    "-c",
    type=TransformConfigParameter(),
    multiple=True,
    metavar="TRANSFORMER_NAME:PARAM=VALUE",
    help="Configure transformers",
)
@click.argument(
    "src",
    nargs=-1,
    type=click.Path(exists=True, file_okay=True, dir_okay=True, readable=True, allow_dash=True),
    metavar="[PATH(S)]",
)
@click.option(
    "--exclude",
    type=str,
    callback=validate_regex_callback,
    help=(
        "A regular expression that matches files and directories that should be"
        " excluded on recursive searches. An empty value means no paths are excluded."
        " Use forward slashes for directories on all platforms."
    ),
    show_default=f"{files.DEFAULT_EXCLUDES}",
)
@click.option(
    "--extend-exclude",
    type=str,
    callback=validate_regex_callback,
    help=(
        "Like **--exclude**, but adds additional files and directories on top of the"
        " excluded ones. (Useful if you simply want to add to the default)"
    ),
)
@click.option(
    "--skip-gitignore",
    is_flag=True,
    show_default=True,
    help="Skip **.gitignore** files and do not ignore files listed inside.",
)
@click.option(
    "--ignore-git-dir",
    is_flag=True,
    help="Ignore **.git** directories when searching for the default configuration file. "
    "By default first parent directory with **.git** directory is returned and this flag disables this behaviour.",
    show_default=True,
)
@click.option(
    "--config",
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        allow_dash=False,
        path_type=str,
    ),
    help="Read configuration from FILE path.",
)
@click.option(
    "--overwrite/--no-overwrite",
    default=None,
    help="Write changes back to file",
    show_default=True,
)
@click.option(
    "--diff",
    is_flag=True,
    help="Output diff of each processed file.",
    show_default=True,
)
@click.option(
    "--color/--no-color",
    default=True,
    help="Enable ANSI coloring the output",
    show_default=True,
)
@click.option(
    "--check",
    is_flag=True,
    help="Don't overwrite files and just return status. Return code 0 means nothing would change. "
    "Return code 1 means that at least 1 file would change. Any internal error will overwrite this status.",
    show_default=True,
)
@click.option(
    "-s",
    "--spacecount",
    type=click.types.INT,
    default=4,
    help="The number of spaces between cells",
    show_default=True,
)
@click.option(
    "--indent",
    type=click.types.INT,
    default=None,
    help="The number of spaces to be used as indentation",
    show_default="same as --spacecount value",
)
@click.option(
    "--continuation-indent",
    type=click.types.INT,
    default=None,
    help="The number of spaces to be used as separator after ... (line continuation) token",
    show_default="same as --spacecount value]",
)
@click.option(
    "-ls",
    "--lineseparator",
    type=click.types.Choice(["native", "windows", "unix", "auto"]),
    default="native",
    help="""
    Line separator to use in the outputs:
    - **native**:  use operating system's native line endings
    - windows: use Windows line endings (CRLF)
    - unix:    use Unix line endings (LF)
    - auto:    maintain existing line endings (uses what's used in the first line)
    """,
    show_default=True,
)
@click.option(
    "--separator",
    type=click.types.Choice(["space", "tab"]),
    default="space",
    help="""
    Token separator to use in the outputs:
    - **space**:   use --spacecount spaces to separate tokens
    - tab:     use a single tabulation to separate tokens
    """,
    show_default=True,
)
@click.option(
    "-sl",
    "--startline",
    default=None,
    type=int,
    help="Limit robotidy only to selected area. If **--endline** is not provided, format text only at **--startline**. "
    "Line numbers start from 1.",
)
@click.option(
    "-el",
    "--endline",
    default=None,
    type=int,
    help="Limit robotidy only to selected area. Line numbers start from 1.",
)
@click.option(
    "--line-length",
    default=120,
    type=int,
    help="Max allowed characters per line",
    show_default=True,
)
@click.option(
    "--list",
    "-l",
    "list_transformers",
    callback=validate_list_optional_value,
    is_flag=False,
    default="",
    flag_value="all",
    help="List available transformers and exit. "
    "Pass optional value **enabled** or **disabled** to filter out list by transformer status.",
)
@click.option(
    "--generate-config",
    is_flag=False,
    default="",
    flag_value="pyproject.toml",
    help="Generate configuration file. Pass optional value to change default config filename.",
    show_default="pyproject.toml",
)
@click.option(
    "--desc",
    "-d",
    default=None,
    metavar="TRANSFORMER_NAME",
    help="Show documentation for selected transformer.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(file_okay=True, dir_okay=False, writable=True, allow_dash=False),
    default=None,
    metavar="PATH",
    help="Use this option to override file destination path.",
)
@click.option("-v", "--verbose", is_flag=True, help="More verbose output", show_default=True)
@click.option(
    "--force-order",
    is_flag=True,
    help="Transform files using transformers in order provided in cli",
)
@click.option(
    "--target-version",
    "-tv",
    type=click.Choice([v.name.lower() for v in misc.TargetVersion], case_sensitive=False),
    callback=validate_target_version_callback,
    help="Only enable transformers supported in set target version",
    show_default="installed Robot Framework version",
)
@click.option(
    "--language",
    "--lang",
    callback=csv_list_type_callback,
    help="Parse Robot Framework files using additional languages.",
    show_default="en",
)
@click.option(
    "--reruns",
    "-r",
    type=int,
    help="Robotidy will rerun the transformations up to reruns times until the code stop changing.",
    show_default="0",
)
@skip.comments_option
@skip.documentation_option
@skip.return_values_option
@skip.keyword_call_option
@skip.keyword_call_pattern_option
@skip.settings_option
@skip.arguments_option
@skip.setup_option
@skip.teardown_option
@skip.timeout_option
@skip.template_option
@skip.return_option
@skip.tags_option
@skip.sections_option
@skip.block_comments_option
@click.version_option(version=version.__version__, prog_name="robotidy")
@click.pass_context
@decorators.catch_exceptions
def cli(ctx: click.Context, **kwargs):
    """
    Robotidy is a tool for formatting Robot Framework source code.
    Full documentation available at <https://robotidy.readthedocs.io> .
    """
    cli_config = RawConfig.from_cli(ctx=ctx, **kwargs)
    global_config = config_module.MainConfig(cli_config)
    global_config.validate_src_is_required()
    if global_config.default.list_transformers:
        print_transformers_list(global_config)
        sys.exit(0)
    if global_config.default.desc is not None:
        return_code = print_description(global_config.default.desc, global_config.default.target_version)
        sys.exit(return_code)
    if global_config.default.generate_config:
        generate_config(global_config)
        sys.exit(0)
    tidy = app.Robotidy(global_config)
    status = tidy.transform_files()
    sys.exit(status)
