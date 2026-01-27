"""
Formatters are classes used to format passed Robot Framework code model.

To create your own formatter you need to create file with the same name as your formatter class. Your class
need to inherit from ``ModelTransformer`` or ``ast.NodeTransformer`` class. Finally put name of your formatter in
``FORMATTERS`` variable in this file.

If you don't want to run your formatter by default and only when calling robocop format with --select YourFormatter
then add ``ENABLED = False`` class attribute inside.
"""

from __future__ import annotations

import copy
import inspect
import pathlib
import textwrap
from typing import TYPE_CHECKING, Any

try:
    import rich_click as click
except ImportError:
    import click

from robot.api.parsing import ModelTransformer
from robot.errors import DataError
from robot.utils.importer import Importer

from robocop.exceptions import ImportFormatterError, InvalidParameterError
from robocop.formatter.skip import SKIP_OPTIONS, Skip, SkipConfig
from robocop.formatter.utils import misc
from robocop.version_handling import ROBOT_VERSION

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

    from robocop.config import WhitespaceConfig
    from robocop.formatter.disablers import DisablersInFile

    try:
        from robot.api import Languages  # RF 6.0+
    except ImportError:
        Languages = type(None)  # Fallback for RF < 6.0

# Type aliases for complicated types
FormatterArgs = dict[str, dict[str, Any]]  # Maps formatter name to its configuration parameters


FORMATTERS = [
    "NormalizeSeparators",
    "DiscardEmptySections",
    "MergeAndOrderSections",
    "RemoveEmptySettings",
    "ReplaceEmptyValues",
    "ReplaceWithVAR",
    "NormalizeAssignments",
    "GenerateDocumentation",
    "OrderSettings",
    "OrderSettingsSection",
    "NormalizeTags",
    "OrderTags",
    "RenameVariables",
    "IndentNestedKeywords",
    "AlignSettingsSection",
    "AlignVariablesSection",
    "AlignTemplatedTestCases",
    "AlignTestCasesSection",
    "AlignKeywordsSection",
    "NormalizeNewLines",
    "NormalizeSectionHeaderName",
    "NormalizeSettingName",
    "ReplaceRunKeywordIf",
    "SplitTooLongLine",
    "SmartSortKeywords",
    "RenameTestCases",
    "RenameKeywords",
    "ReplaceBreakContinue",
    "InlineIf",
    "Translate",
    "NormalizeComments",
]

IMPORTER = Importer()


class FormatterParameter:
    def __init__(self, name: str, default_value: Any) -> None:
        self.name = name
        self.value = default_value

    def __str__(self) -> str:
        if self.value is not None and str(self.value) != "":
            return f"{self.name} : {self.value}"
        return self.name


class FormatterContainer:
    """Stub for a formatter container class that holds the formatter instance and its metadata."""

    def __init__(self, instance: ModelTransformer, argument_names: list[str], spec: Any, args: dict[str, Any]) -> None:
        self.instance = instance
        self.name = instance.__class__.__name__
        self.enabled_by_default = getattr(instance, "ENABLED", True)
        self.parameters = self.get_parameters(argument_names, spec)
        self.args = args

    def get_parameters(self, argument_names: list[str], spec: Any) -> list[FormatterParameter]:
        params = []
        for arg in argument_names:
            if arg == "enabled":
                default = self.enabled_by_default
            else:
                default = spec.defaults.get(arg, None)
            params.append(FormatterParameter(arg, default))
        return params

    def __str__(self) -> str:
        s = f"## Formatter {self.name}\n" + textwrap.dedent(self.instance.__doc__)
        if self.parameters:
            s += "\nSupported parameters:\n  - " + "\n - ".join(str(param) for param in self.parameters) + "\n"
        s += f"\nSee <https://robocop.dev/stable/formatter/formatters/{self.name}/> for more examples."
        return s


class Formatter(ModelTransformer):
    # Injected at runtime
    skip: Skip
    formatting_config: WhitespaceConfig
    disablers: DisablersInFile
    languages: Languages
    config_directory: Path

    def __init__(self) -> None:
        self.formatters: dict[str, ModelTransformer] = {}


def get_formatter_short_name(name: str) -> str:
    """
    Remove module path or file extension for better printing the errors.

    Examples:
       ShortName -> ShortName
       import.path.formatter -> formatter
       C://path/to/formatter.py -> formatter

    """
    if name.endswith(".py"):
        return pathlib.Path(name).stem
    return name.rsplit(".")[-1]


def get_absolute_path_to_formatter(name: str) -> str | pathlib.Path:
    """Return an absolute path to the formatter if it's not a default formatter."""
    if pathlib.Path(name).exists():
        return pathlib.Path(name).resolve()
    return name


def load_formatters_from_module(module: Any) -> dict[str, type[ModelTransformer]]:
    classes = inspect.getmembers(module, inspect.isclass)
    return {
        name: formatter_class
        for name, formatter_class in classes
        if issubclass(formatter_class, (Formatter, ModelTransformer))
        and formatter_class
        not in (
            Formatter,
            ModelTransformer,
        )
    }


def order_formatters(formatters: dict[str, type[ModelTransformer]], module: Any) -> dict[str, type[ModelTransformer]]:
    """If the module contains FORMATTERS list, order formatters using this list."""
    formatters_list = getattr(module, "FORMATTERS", [])
    if not (formatters_list and isinstance(formatters_list, list)):
        return formatters
    ordered_formatters = {}
    for name in formatters_list:
        if name not in formatters:
            raise ImportFormatterError(
                f"Importing formatter '{name}' declared in FORMATTERS list failed. Verify if correct name was provided."
            ) from None
        ordered_formatters[name] = formatters[name]
    return ordered_formatters


def import_formatter(
    name: str, formatter_args: FormatterArgs, skip_config: SkipConfig
) -> Generator[FormatterContainer, None, None]:
    if name in FORMATTERS:
        yield from import_default_formatter(name, formatter_args, skip_config)
    else:
        yield from import_custom_formatter(name, formatter_args, skip_config)


def import_default_formatter(
    name: str, formatter_args: FormatterArgs, skip_config: SkipConfig
) -> Generator[FormatterContainer, None, None]:
    import_path = f"robocop.formatter.formatters.{name}"
    imported = IMPORTER.import_class_or_module(import_path)
    yield create_formatter_instance(imported, name, formatter_args.get(name, {}), skip_config)


def import_custom_formatter(
    name: str, formatter_args: FormatterArgs, skip_config: SkipConfig
) -> Generator[FormatterContainer, None, None]:
    try:
        short_name = get_formatter_short_name(name)
        abs_path = get_absolute_path_to_formatter(name)
        imported = IMPORTER.import_class_or_module(abs_path)
        if inspect.isclass(imported):
            yield create_formatter_instance(imported, short_name, formatter_args.get(short_name, {}), skip_config)
        else:
            formatters = load_formatters_from_module(imported)
            formatters = order_formatters(formatters, imported)
            for formatter_name, formatter_class in formatters.items():
                yield create_formatter_instance(
                    formatter_class, formatter_name, formatter_args.get(formatter_name, {}), skip_config
                )
    except DataError:
        similar_finder = misc.RecommendationFinder()
        similar = similar_finder.find_similar(short_name, FORMATTERS)
        raise ImportFormatterError(
            f"Importing formatter '{short_name}' failed. Verify if correct name or configuration was provided.{similar}"
        ) from None


def create_formatter_instance(
    imported_class: type[ModelTransformer], short_name: str, args: dict[str, Any], skip_config: SkipConfig
) -> FormatterContainer:
    spec = IMPORTER._get_arg_spec(imported_class)  # noqa: SLF001
    handles_skip: frozenset[str] = getattr(imported_class, "HANDLES_SKIP", frozenset())
    positional, named, argument_names, skip = resolve_args(
        short_name, spec, args, skip_config, handles_skip=handles_skip
    )
    instance = imported_class(*positional, **named)
    instance.skip = skip
    return FormatterContainer(instance, argument_names, spec, args)


def split_args_to_class_and_skip(args: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    filtered_args = {}
    skip_args = {}
    for arg, value in args.items():
        if arg == "enabled":
            continue
        if arg in SKIP_OPTIONS:
            skip_args[arg.replace("skip_", "")] = value
        else:
            filtered_args[arg] = value
    return filtered_args, skip_args


def resolve_argument_names(argument_names: list[str], handles_skip: frozenset[str]) -> list[str]:
    """Get formatter argument names with resolved skip parameters."""
    new_args = ["enabled"]
    if "skip" not in argument_names:
        return new_args + argument_names
    new_args.extend([arg for arg in argument_names if arg != "skip"])
    new_args.extend(arg for arg in sorted(handles_skip) if arg not in new_args)
    return new_args


def assert_handled_arguments(formatter: str, args: dict[str, Any], argument_names: list[str]) -> None:
    """
    Check if provided arguments are handled by given formatter.

    Raises InvalidParameterError if arguments does not match.
    """
    for arg in args:
        # it's fine to only check for first non-matching parameter
        if arg not in argument_names:
            similar_finder = misc.RecommendationFinder()
            similar = similar_finder.find_similar(arg, argument_names)
            if not similar and argument_names:
                arg_names = "\n    " + "\n    ".join(argument_names)
                similar = f" This formatter accepts following arguments:{arg_names}"
            raise InvalidParameterError(formatter, similar) from None


def get_skip_args_from_spec(spec: Any) -> dict[str, Any]:
    """
    Retrieve skip-like options from the class signature.

    It is possible to override default skip value (such as skip_documentation
    from False to True in AlignKeywordsSection).
    This method iterate over spec and finds such overrides.
    """
    defaults = {}
    for arg, value in spec.defaults.items():
        if arg in SKIP_OPTIONS:
            defaults[arg.replace("skip_", "")] = value
    return defaults


def get_skip_class(spec: Any, skip_args: dict[str, Any], global_skip: SkipConfig) -> Skip:
    defaults = get_skip_args_from_spec(spec)
    defaults.update(skip_args)
    skip_config = copy.deepcopy(global_skip)
    skip_config.update_with_str_config(**defaults)
    return Skip(skip_config)


def resolve_args(
    formatter: str, spec: Any, args: dict[str, Any], global_skip: SkipConfig, handles_skip: frozenset[str]
) -> tuple[list[Any], dict[str, Any], list[str], Skip]:
    """
    Use class definition to identify which arguments from the configuration should be used to invoke it.

    First, we're splitting arguments into class arguments and skip arguments (those that are handled by Skip class).
    Class arguments are resolved with their definition, and if a class accepts the "skip" parameter, the Skip class
    will be also added to class arguments.
    """
    class_args, skip_args = split_args_to_class_and_skip(args)
    spec_args = list(spec.argument_names)
    argument_names = resolve_argument_names(spec_args, handles_skip)
    assert_handled_arguments(formatter, class_args, argument_names)
    try:
        args_list = [f"{arg}={value}" for arg, value in class_args.items()]
        positional, named = spec.resolve(args_list)
        named = dict(named)
        skip = get_skip_class(spec, skip_args, global_skip)
    except ValueError as err:
        raise InvalidParameterError(formatter, f" {err}") from None
    else:
        return positional, named, argument_names, skip


def can_run_in_robot_version(formatter: ModelTransformer, overwritten: bool, target_version: int) -> bool:
    if not hasattr(formatter, "MIN_VERSION"):
        return True
    if target_version >= formatter.MIN_VERSION:
        return True
    if overwritten:
        # --select FormatterDisabledInVersion or --configure FormatterDisabledInVersion.enabled=True
        if target_version == ROBOT_VERSION.major:
            click.echo(
                f"{formatter.__class__.__name__} formatter requires Robot Framework {formatter.MIN_VERSION}.* "
                f"version but you have {ROBOT_VERSION} installed. "
                f"Upgrade installed Robot Framework if you want to use this formatter.",
                err=True,
            )
        else:
            click.echo(
                f"{formatter.__class__.__name__} formatter requires Robot Framework {formatter.MIN_VERSION}.* "
                f"version but you set --target-version rf{target_version}. "
                f"Set --target-version to {formatter.MIN_VERSION} or do not forcefully enable this formatter "
                f"with --select / enable parameter.",
                err=True,
            )
    return False
