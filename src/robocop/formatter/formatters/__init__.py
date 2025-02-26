"""
Formatters are classes used to transform passed Robot Framework code model.

To create your own formatter you need to create file with the same name as your formatter class. Your class
need to inherit from ``ModelFormatter`` or ``ast.NodeFormatter`` class. Finally put name of your formatter in
``TRANSFORMERS`` variable in this file.

If you don't want to run your formatter by default and only when calling robocop format with --transform YourFormatter
then add ``ENABLED = False`` class attribute inside.
"""

from __future__ import annotations

import copy
import inspect
import pathlib
import textwrap
from collections.abc import Iterable
from itertools import chain

try:
    import rich_click as click
except ImportError:
    import click

from robot.api.parsing import ModelFormatter
from robot.errors import DataError
from robot.utils.importer import Importer
from robocop.formatter.exceptions import ImportFormatterError, InvalidParameterError, InvalidParameterFormatError
from robocop.formatter.skip import Skip, SkipConfig
from robocop.formatter.utils import misc

FORMATTERS = [
    "AddMissingEnd",
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
    "ReplaceReturns",
    "ReplaceBreakContinue",
    "InlineIf",
    "Translate",
    "NormalizeComments",
]


IMPORTER = Importer()


class FormatConfig:
    def __init__(self, config, force_include, custom_formatter, is_config):
        name, args = misc.split_args_from_name_or_path(config)
        self.name = name.strip()
        self.args = self.convert_args(args)
        self.force_include = force_include
        self.custom_formatter = custom_formatter
        self.is_config_only = is_config
        self.duplicate_reported = False

    def convert_args(self, args):
        """
        Convert list of param=value arguments to dictionary.
        """
        converted = dict()
        for arg in args:
            try:
                param, value = arg.split("=", maxsplit=1)
                param, value = param.strip(), value.strip()
            except ValueError:
                raise InvalidParameterFormatError(self.name) from None
            if param == "enabled":
                converted[param] = value.lower() == "true"
            else:
                converted[param] = value
        return converted

    def join_formatter_configs(self, formatter_config: FormatConfig):
        """
        Join 2 configurations i.e. from --transform, --load-formatters or --config.
        """
        if self.force_include and formatter_config.force_include:
            if not self.duplicate_reported:
                click.echo(
                    f"Duplicated formatter '{self.name}' in the transform option. "
                    f"It will be run only once with the configuration from the last transform."
                )
                self.duplicate_reported = True
        self.is_config_only = self.is_config_only and formatter_config.is_config_only
        self.force_include = self.force_include or formatter_config.force_include
        self.custom_formatter = self.custom_formatter or formatter_config.custom_formatter
        self.join_args(formatter_config)

    def join_args(self, formatter_config: FormatConfig):
        self.args.update(formatter_config.args)


class FormatConfigMap:
    """
    Collection of all formatters and their configs.
    """

    def __init__(
        self,
        transform: list[FormatConfig],
        custom_formatters: list[FormatConfig],
        config: list[FormatConfig],
    ):
        self.force_included_only = False
        self.formatters: dict[str, FormatConfig] = dict()
        for tr in chain(transform, custom_formatters, config):
            self.add_formatter(tr)

    def add_formatter(self, tr):
        if tr.force_include:
            self.force_included_only = True
        if tr.name in self.formatters:
            self.formatters[tr.name].join_formatter_configs(tr)
        else:
            self.formatters[tr.name] = tr

    def get_args(self, *names) -> dict:
        for name in names:
            name = str(name)
            if name in self.formatters:
                return self.formatters[name].args
        return dict()

    def formatter_should_be_included(self, name: str) -> bool:
        """
        Check whether --transform option was used. If it was, check if formatter name was used with --transform.
        """
        if not self.force_included_only:
            return True
        return self.formatter_is_force_included(name)

    def formatter_is_force_included(self, name: str) -> bool:
        return name in self.formatters and self.formatters[name].force_include

    def formatter_was_forcefully_enabled(self, name: str) -> bool:
        if name not in self.formatters:
            return False
        return self.formatters[name].force_include or self.formatters[name].args.get("enabled", False)

    def update_with_defaults(self, defaults: list[str]):
        for default in defaults:
            if default in self.formatters:
                self.formatters[default].is_config_only = False
            else:
                self.formatters[default] = FormatConfig(default, False, False, False)

    def order_using_list(self, order: list[str]):
        temp_formatters: dict[str, FormatConfig] = dict()
        for name in order:
            if name in self.formatters:
                temp_formatters[name] = self.formatters[name]
        for name, formatter in self.formatters.items():
            if name not in temp_formatters:
                temp_formatters[name] = formatter
        self.formatters = temp_formatters

    def validate_config_names(self):
        """
        Assert that all --configure NAME are either defaults or from --transform/--load-formatter.
        Otherwise, raise an error with similar names.
        """
        # TODO: Currently not used. It enforces that every --config NAME is valid one which may not be desired
        # if the NAME is external formatter which may not be imported.
        # Maybe we can add special flag like --validate-config that would run this method if needed.
        for transf_name, formatter in self.formatters.items():
            if not formatter.is_config_only:
                continue
            similar_finder = misc.RecommendationFinder()
            formatter_names = [name for name, transf in self.formatters.items() if not transf.is_config_only]
            similar = similar_finder.find_similar(transf_name, formatter_names)
            raise ImportFormatterError(
                f"Configuring formatter '{transf_name}' failed. " f"Verify if correct name was provided.{similar}"
            ) from None


def convert_transform_config(value: str, param_name: str) -> FormatConfig:
    force_included = param_name == "transform"
    custom_formatter = param_name == "custom_formatters"
    is_config = param_name == "configure"
    return FormatConfig(
        value, force_include=force_included, custom_formatter=custom_formatter, is_config=is_config
    )


class FormatConfigParameter(click.ParamType):
    """
    Click parameter that holds the name of the formatter and optional configuration.
    """

    name = "transform"

    def convert(self, value, param, ctx):
        return convert_transform_config(value, param.name)


class FormatterParameter:
    def __init__(self, name, default_value):
        self.name = name
        self.value = default_value

    def __str__(self):
        if self.value is not None and str(self.value) != "":
            return f"{self.name} : {self.value}"
        return self.name


class FormatterContainer:
    """
    Stub for formatter container class that holds the formatter instance and its metadata.
    """

    def __init__(self, instance, argument_names, spec, args):
        self.instance = instance
        self.name = instance.__class__.__name__
        self.enabled_by_default = getattr(instance, "ENABLED", True)
        self.parameters = self.get_parameters(argument_names, spec)
        self.args = args

    def get_parameters(self, argument_names, spec):
        params = []
        for arg in argument_names:
            if arg == "enabled":
                default = self.enabled_by_default
            else:
                default = spec.defaults.get(arg, None)
            params.append(FormatterParameter(arg, default))
        return params

    def __str__(self):
        s = f"## Formatter {self.name}\n" + textwrap.dedent(self.instance.__doc__)
        if self.parameters:
            s += "\nSupported parameters:\n  - " + "\n - ".join(str(param) for param in self.parameters) + "\n"
        s += f"\nSee <https://robotidy.readthedocs.io/en/latest/formatters/{self.name}.html> for more examples."  # FIXME
        return s


class Formatter(ModelFormatter):
    def __init__(self, skip: Skip | None = None):
        self.formatting_config = None  # to make lint happy (we're injecting the configs)
        self.languages = None
        self.formatters: dict = dict()
        self.disablers = None
        self.config_directory = None
        self.skip = skip


def get_formatter_short_name(name):
    """Removes module path or file extension for better printing the errors."""
    if name.endswith(".py"):
        return name.split(".")[-2]
    return name.split(".")[-1]


def get_absolute_path_to_formatter(name, short_name):
    """
    If the formatter is not default one, try to get absolute path to formatter to make it easier to import it.
    """
    if short_name in TRANSFORMERS:
        return name
    if pathlib.Path(name).exists():
        return pathlib.Path(name).resolve()
    return name


def load_formatters_from_module(module):
    classes = inspect.getmembers(module, inspect.isclass)
    formatters = dict()
    for name, formatter_class in classes:
        if issubclass(formatter_class, (Formatter, ModelFormatter)) and formatter_class not in (
            Formatter,
            ModelFormatter,
        ):
            formatters[name] = formatter_class
    return formatters


def order_formatters(formatters, module):
    """If the module contains FORMATTERS list, order formatters using this list."""
    formatters_list = getattr(module, "FORMATTERS", [])
    if not (formatters_list and isinstance(formatters_list, list)):
        return formatters
    ordered_formatters = dict()
    for name in formatters_list:
        if name not in formatters:
            raise ImportFormatterError(
                f"Importing formatter '{name}' declared in TRANSFORMERS list failed. "
                "Verify if correct name was provided."
            ) from None
        ordered_formatters[name] = formatters[name]
    return ordered_formatters


def import_formatter(name, config: FormatConfigMap, skip) -> Iterable[FormatterContainer]:
    import_path = resolve_core_import_path(name)
    short_name = get_formatter_short_name(import_path)
    name = get_absolute_path_to_formatter(import_path, short_name)
    try:
        imported = IMPORTER.import_class_or_module(name)
        if inspect.isclass(imported):
            yield create_formatter_instance(
                imported, short_name, config.get_args(name, short_name, import_path), skip
            )
        else:
            formatters = load_formatters_from_module(imported)
            formatters = order_formatters(formatters, imported)
            for name, formatter_class in formatters.items():
                yield create_formatter_instance(
                    formatter_class, name, config.get_args(name, short_name, import_path), skip
                )
    except DataError:
        similar_finder = misc.RecommendationFinder()
        similar = similar_finder.find_similar(short_name, TRANSFORMERS)
        raise ImportFormatterError(
            f"Importing formatter '{short_name}' failed. "
            f"Verify if correct name or configuration was provided.{similar}"
        ) from None


def create_formatter_instance(imported_class, short_name, args, skip):
    spec = IMPORTER._get_arg_spec(imported_class)
    handles_skip = getattr(imported_class, "HANDLES_SKIP", {})
    positional, named, argument_names = resolve_args(short_name, spec, args, skip, handles_skip=handles_skip)
    instance = imported_class(*positional, **named)
    return FormatterContainer(instance, argument_names, spec, args)


def split_args_to_class_and_skip(args):
    filtered_args = []
    skip_args = {}
    for arg, value in args.items():
        if arg == "enabled":
            continue
        if arg in SkipConfig.HANDLES:
            skip_args[arg.replace("skip_", "")] = value
        else:
            filtered_args.append(f"{arg}={value}")
    return filtered_args, skip_args


def resolve_argument_names(argument_names: list[str], handles_skip):
    """Get formatter argument names with resolved skip parameters."""
    new_args = ["enabled"]
    if "skip" not in argument_names:
        return new_args + argument_names
    new_args.extend([arg for arg in argument_names if arg != "skip"])
    new_args.extend(arg for arg in sorted(handles_skip) if arg not in new_args)
    return new_args


def assert_handled_arguments(formatter, args, argument_names):
    """
    Check if provided arguments are handled by given formatter.
    Raises InvalidParameterError if arguments does not match.
    """
    arg_names = [arg.split("=")[0] for arg in args]
    for arg in arg_names:
        # it's fine to only check for first non-matching parameter
        if arg not in argument_names:
            similar_finder = misc.RecommendationFinder()
            similar = similar_finder.find_similar(arg, argument_names)
            if not similar and argument_names:
                arg_names = "\n    " + "\n    ".join(argument_names)
                similar = f" This formatter accepts following arguments:{arg_names}"
            raise InvalidParameterError(formatter, similar) from None


def get_skip_args_from_spec(spec):
    """
    It is possible to override default skip value (such as skip_documentation
    from False to True in AlignKeywordsSection).
    This method iterate over spec and finds such overrides.
    """
    defaults = dict()
    for arg, value in spec.defaults.items():
        if arg in SkipConfig.HANDLES:
            defaults[arg.replace("skip_", "")] = value
    return defaults


def get_skip_class(spec, skip_args, global_skip):
    defaults = get_skip_args_from_spec(spec)
    defaults.update(skip_args)
    if global_skip is None:
        skip_config = SkipConfig()
    else:
        skip_config = copy.deepcopy(global_skip)
    skip_config.update_with_str_config(**defaults)
    return Skip(skip_config)


def resolve_args(formatter, spec, args, global_skip, handles_skip):
    """
    Use class definition to identify which arguments from configuration
    should be used to invoke it.

    First we're splitting arguments into class arguments and skip arguments
    (those that are handled by Skip class).
    Class arguments are resolved with their definition and if class accepts
    "skip" parameter the Skip class will be also added to class arguments.
    """
    args, skip_args = split_args_to_class_and_skip(args)
    spec_args = list(spec.argument_names)
    argument_names = resolve_argument_names(spec_args, handles_skip)
    assert_handled_arguments(formatter, args, argument_names)
    try:
        positional, named = spec.resolve(args)
        named = dict(named)
        if "skip" in spec_args:
            named["skip"] = get_skip_class(spec, skip_args, global_skip)
        return positional, named, argument_names
    except ValueError as err:
        raise InvalidParameterError(formatter, f" {err}") from None


def resolve_core_import_path(name):
    """Append import path if formatter is core Robotidy formatter."""
    return f"robocop.formatter.formatters.{name}" if name in TRANSFORMERS else name


def can_run_in_robot_version(formatter, overwritten, target_version):
    if not hasattr(formatter, "MIN_VERSION"):
        return True
    if target_version >= formatter.MIN_VERSION:
        return True
    if overwritten:
        # --transform FormatterDisabledInVersion or --configure FormatterDisabledInVersion:enabled=True
        if target_version == misc.ROBOT_VERSION.major:
            click.echo(
                f"{formatter.__class__.__name__} formatter requires Robot Framework {formatter.MIN_VERSION}.* "
                f"version but you have {misc.ROBOT_VERSION} installed. "
                f"Upgrade installed Robot Framework if you want to use this formatter.",
                err=True,
            )
        else:
            click.echo(
                f"{formatter.__class__.__name__} formatter requires Robot Framework {formatter.MIN_VERSION}.* "
                f"version but you set --target-version rf{target_version}. "
                f"Set --target-version to rf{formatter.MIN_VERSION} or do not forcefully enable this formatter "
                f"with --transform / enable parameter.",
                err=True,
            )
    return False


def load_formatters(
    formatters_config: FormatConfigMap,
    target_version,
    skip=None,
    allow_disabled=False,
    force_order=False,
    allow_version_mismatch=True,
):
    """Dynamically load all classes from this file with attribute `name` defined in selected_formatters"""
    loaded_formatters = []
    formatters_config.update_with_defaults(TRANSFORMERS)
    if not force_order:
        formatters_config.order_using_list(TRANSFORMERS)
    for name, formatter_config in formatters_config.formatters.items():
        if not allow_disabled and not formatters_config.formatter_should_be_included(name):
            continue
        for container in import_formatter(name, formatters_config, skip):
            if formatters_config.force_included_only:
                enabled = container.args.get("enabled", True)
            elif "enabled" in container.args:
                enabled = container.args["enabled"]
            else:
                enabled = getattr(container.instance, "ENABLED", True)
            if not (enabled or allow_disabled):
                continue
            if can_run_in_robot_version(
                container.instance,
                overwritten=formatters_config.formatter_was_forcefully_enabled(name),
                target_version=target_version,
            ):
                container.enabled_by_default = enabled
                loaded_formatters.append(container)
            elif allow_version_mismatch and allow_disabled:
                container.instance.ENABLED = False
                container.enabled_by_default = False
                loaded_formatters.append(container)
    return loaded_formatters
