from __future__ import annotations

import importlib.util
import inspect
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from robocop import exceptions, plugins
from robocop.config import defaults
from robocop.config.builder import ConfigBuilder
from robocop.linter.utils.misc import get_robocop_cache_directory, str2bool
from robocop.runtime.resolver import LinterImporter

if TYPE_CHECKING:
    from robocop.config.schema import Config
    from robocop.linter.diagnostics import Diagnostics


class Report:
    """
    Base class for report class.

    Override the ` configure ` method if you want to allow report configuration.

    Set class attribute `NO_ALL` to `False` if you don't want your report to be included in `all` reports.
    """

    NO_ALL = True
    ENABLED = False
    INTERNAL = False
    name: str  # Set by subclasses
    description: str  # Set by subclasses

    def __init__(self, config: Config) -> None:
        self.config = config

    def configure(self, name: str, value: str) -> None:  # noqa: ARG002
        raise exceptions.ConfigurationError(f"Provided param '{name}' for report '{self.name}' does not exist")

    def generate_report(self, **kwargs: Any) -> None:
        raise NotImplementedError


class FileReport(Report):
    """Base class for a report that saves its output to a file."""

    def __init__(self, config: Config, skip_on_empty: bool = False) -> None:
        self.skip_on_empty = skip_on_empty
        super().__init__(config)

    def configure(self, name: str, value: str) -> None:
        if name == "skip_on_empty":
            self.skip_on_empty = str2bool(value)
        else:
            super().configure(name, value)

    def should_skip(self, diagnostics: Diagnostics) -> bool:
        """
        Check if the report file generation should be skipped.

        Returns:
            True if the report is configured with ``skip_on_empty`` and there are no issues to report.

        """
        return self.skip_on_empty and not diagnostics.diagnostics


class JsonFileReport(FileReport):
    """Base class for a report that generates a json-based file."""

    def __init__(self, output_path: str, config: Config, skip_on_empty: bool = False) -> None:
        self.output_path = output_path
        super().__init__(config, skip_on_empty=skip_on_empty)

    def configure(self, name: str, value: str) -> None:
        if name == "output_path":
            self.output_path = value
        else:
            super().configure(name, value)

    def generate_report_with_type(self, report: list[dict[str, Any]] | dict[str, Any], report_type: str) -> None:
        output_path = Path(self.output_path)
        try:
            output_path.parent.mkdir(exist_ok=True, parents=True)
            with open(output_path, "w") as fp:
                json.dump(report, fp, indent=4)
        except OSError as err:
            raise exceptions.FatalError(f"Failed to write {report_type} report to {output_path}: {err}") from None
        print(f"Generated {report_type} report at {self.output_path}")


class ComparableReport(Report):
    def __init__(self, config: Config) -> None:
        self.compare_runs = config.linter.compare
        super().__init__(config)

    def generate_report(self, **kwargs: Any) -> None:
        raise NotImplementedError

    def persist_result(self) -> Any:
        raise NotImplementedError


def _load_reports_from_paths(config: Config, paths: list[str | Path]) -> dict[str, Report]:
    """
    Load all valid reports from the given paths.

    Report is considered valid if it inherits from the ` Report ` class
    and contains both `name` and `description` attributes.
    """
    loaded_reports: dict[str, Report] = {}
    # TODO: Move report loading to resolver
    robocop_importer = LinterImporter()
    for module in robocop_importer.modules_from_paths(paths):
        classes = inspect.getmembers(module, inspect.isclass)
        for report_class in classes:
            if not issubclass(report_class[1], Report):
                continue
            if report_class[1].__module__ == __name__:  # base classes imported by the module
                continue
            report = report_class[1](config)
            if not hasattr(report, "name") or not hasattr(report, "description"):
                continue
            loaded_reports[report.name] = report
    return loaded_reports


def load_reports(config: Config) -> dict[str, Report]:
    """Load all valid, internal reports."""
    return _load_reports_from_paths(config, [Path(__file__).parent])


def is_custom_report_source(name: str) -> bool:
    """
    Check if the value configured with ``--reports`` points to the source with the custom reports.

    Custom reports are loaded from the plugin reference (``example.reports``), importable module
    (``package.reports``) or a path to the Python file or a directory with the reports.
    """
    if name in {"all", "None"}:
        return False
    if plugins.resolve_module_reference(name) is not None:
        return True
    if "." in name or "/" in name or "\\" in name:
        return True
    return Path(name).is_dir()


def load_custom_reports(config: Config, sources: list[str]) -> dict[str, Report]:
    """Load reports from the custom sources: plugins, importable modules or paths."""
    if not sources:
        return {}
    for source in sources:
        _validate_custom_report_source(source)
    return _load_reports_from_paths(config, list(sources))


def _validate_custom_report_source(source: str) -> None:
    """Raise an error if the custom report source cannot be resolved to a plugin, path or a module."""
    if plugins.resolve_module_reference(source) is not None or Path(source).exists():
        return
    try:
        if importlib.util.find_spec(source) is not None:
            return
    except (ImportError, AttributeError, ValueError):
        pass
    raise exceptions.InvalidCustomReportSource(source)


def load_all_reports(config: Config) -> dict[str, Report]:
    """Load internal reports together with the custom reports configured with ``--reports``."""
    reports = load_reports(config)
    sources = [name for name in _iter_configured_reports(config) if is_custom_report_source(name)]
    for name, report in load_custom_reports(config, sources).items():
        if name not in reports:
            reports[name] = report
    return reports


def _iter_configured_reports(config: Config) -> list[str]:
    """Return reports configured with ``--reports``, with the comma separated values split."""
    return [csv_report for report in config.linter.reports for csv_report in report.split(",")]


def get_reports(config: Config) -> dict[str, Report]:
    """
    Return the dictionary with a list of valid, enabled reports (listed in `configured_reports` set of str).

    If `configured_reports` contains `all`, then all default reports are enabled.

    Values that point to the custom reports source (plugin, module or path) load and enable all reports
    defined in such source.
    """
    configured_reports = _iter_configured_reports(config)
    if "None" in configured_reports:
        configured_reports = []
    custom_reports_by_source: dict[str, dict[str, Report]] = {
        source: load_custom_reports(config, [source])
        for source in dict.fromkeys(configured_reports)
        if is_custom_report_source(source)
    }
    reports = load_reports(config)
    for source_reports in custom_reports_by_source.values():
        for name, report_class in source_reports.items():
            if name in reports:
                raise exceptions.ConfigurationError(
                    f"Custom report '{name}' has the same name as the existing Robocop report."
                )
            reports[name] = report_class
    enabled_reports = {name: report_class for name, report_class in reports.items() if report_class.ENABLED}
    for report in configured_reports:
        if report in custom_reports_by_source:  # custom reports are enabled by loading them
            for name, report_class in custom_reports_by_source[report].items():
                if name not in enabled_reports:
                    enabled_reports[name] = report_class
        elif report == "all":
            for name, report_class in reports.items():
                if report_class.NO_ALL and name not in enabled_reports:
                    enabled_reports[name] = report_class
        elif report not in reports:
            raise exceptions.InvalidReportName(report, reports)
        elif report not in enabled_reports:
            enabled_reports[report] = reports[report]
    for report, report_class in reports.items():
        if report_class.ENABLED and report not in enabled_reports:
            enabled_reports[report] = report_class
    return enabled_reports


def print_reports(reports: dict[str, Report], only_enabled: bool | None, config: Config | None = None) -> str:
    """
    Return description of reports.

    The report list is filtered and only public reports are provided. If the report is enabled in the current
    configuration, it will have (enabled) suffix (and (disabled) if it is disabled).

    Args:
        reports: Dictionary with loaded reports.
        only_enabled: if set to True/False, it will filter reports by enabled/disabled status
        config: configuration used to load reports. Required to list custom reports.

    """
    if config is None:
        config = ConfigBuilder().from_raw(None, None)
    all_reports = load_all_reports(config)
    for name, report in reports.items():  # custom reports enabled in the runtime configuration
        all_reports.setdefault(name, report)
    all_public_reports = [report for report in all_reports.values() if not report.INTERNAL]
    all_public_reports = sorted(all_public_reports, key=lambda x: x.name)
    configured_reports = {x.name for x in reports.values()}
    available_reports = ""
    for report in all_public_reports:
        is_enabled = report.name in configured_reports
        if only_enabled is not None and only_enabled != is_enabled:
            continue
        status = "[green]enabled[/green]" if is_enabled else "[red]disabled[/red]"
        if not report.NO_ALL and not report.INTERNAL:
            status += " - not included in all"
        available_reports += f"\n{report.name:20} - {report.description} ({status})"
    if available_reports:
        available_reports = "Available reports:" + available_reports
    else:
        available_reports = "No available reports that meet your search criteria."
    available_reports += (
        "\n\nEnable report by passing report name using --reports option. "
        "Use `all` to enable all default reports. "
        "Non-default reports can be only enabled using report name."
    )
    return available_reports


def load_reports_result_from_cache() -> dict[str, Any] | None:
    cache_dir = get_robocop_cache_directory(ensure_exists=False)
    cache_file = cache_dir / defaults.ROBOCOP_CACHE_FILE
    if not cache_file.is_file():
        return None
    with open(cache_file) as fp:
        try:
            result: dict[str, Any] = json.load(fp)
        except json.JSONDecodeError:
            return None
        else:
            return result


def save_reports_result_to_cache(working_dir: str, report_results: dict[str, Any]) -> None:
    """
    Save results from Robocop reports to JSON file.

    The result file contains results grouped using a working directory.
    That's why we are loading previous results and overwriting only
    the results for the current working directory.
    """
    cache_dir = get_robocop_cache_directory(ensure_exists=True)
    cache_file = cache_dir / defaults.ROBOCOP_CACHE_FILE
    prev_results = load_reports_result_from_cache()
    if prev_results is None:
        prev_results = {}
    prev_results[working_dir] = report_results
    with open(cache_file, "w") as fp:
        json_string = json.dumps(prev_results, indent=4)
        fp.write(json_string)
