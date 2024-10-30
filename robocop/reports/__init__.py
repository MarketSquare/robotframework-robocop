import inspect
import json
from collections import OrderedDict
from pathlib import Path

import robocop.exceptions
from robocop.checkers import RobocopImporter
from robocop.utils.misc import get_robocop_cache_directory

ROBOCOP_CACHE_FILE = ".robocop_cache"


class Report:
    """
    Base class for report class.
    Override `configure` method if you want to allow report configuration.
    Override `add_message`` if your report processes the Robocop issues.

    Set class attribute `DEFAULT` to `False` if you don't want your report to be included in `all` reports.
    """

    DEFAULT = True
    INTERNAL = False
    COMPARE_RESULTS = False

    def configure(self, name, value):
        raise robocop.exceptions.ConfigGeneralError(
            f"Provided param '{name}' for report '{getattr(self, 'name')}' does not exist"
        )

    def add_message(self, *args):
        pass

    def get_report(self, *args):
        return None


class ComparableReport(Report):
    COMPARE_RESULTS = True

    def __init__(self, compare_runs):
        self.compare_runs = compare_runs

    def get_report(self, prev_results):
        raise NotImplementedError

    def persist_result(self):
        raise NotImplementedError


def load_reports(compare_runs=False):
    """
    Load all valid reports.
    Report is considered valid if it inherits from `Report` class
    and contains both `name` and `description` attributes.
    """
    reports = {}
    robocop_importer = RobocopImporter()
    for module in robocop_importer.modules_from_paths([Path(__file__).parent]):
        classes = inspect.getmembers(module, inspect.isclass)
        for report_class in classes:
            if not issubclass(report_class[1], Report):
                continue
            if is_report_comparable(report_class[1]):
                report = report_class[1](compare_runs)
            else:
                report = report_class[1]()
            if not hasattr(report, "name") or not hasattr(report, "description"):
                continue
            reports[report.name] = report
    return reports


def is_report_comparable(report):
    return getattr(report, "COMPARE_RESULTS", False)


def is_report_default(report):
    return getattr(report, "DEFAULT", False)


def is_report_internal(report):
    return getattr(report, "INTERNAL", False)


def disable_external_reports_if_none(configured_reports: list[str]) -> list[str]:
    """If any reports is 'None', disable other reports other than internal reports."""
    if "None" in configured_reports:
        if "internal_json_report" in configured_reports:
            # TODO: Improve how internal reports are handled
            return ["return_status", "internal_json_report"]
        return ["return_status"]
    return configured_reports


def get_reports(configured_reports):
    """
    Return dictionary with list of valid, enabled reports (listed in `configured_reports` set of str).
    If `configured_reports` contains `all` then all default reports are enabled.
    """
    configured_reports = disable_external_reports_if_none(configured_reports)
    compare_runs = "compare_runs" in configured_reports
    reports = load_reports(compare_runs)
    enabled_reports = OrderedDict()
    for report in configured_reports:
        if report == "all":
            for name, report_class in reports.items():
                if is_report_default(report_class) and name not in enabled_reports:
                    enabled_reports[name] = report_class
        elif report not in reports:
            raise robocop.exceptions.InvalidReportName(report, reports)
        elif report not in enabled_reports:
            enabled_reports[report] = reports[report]
    return enabled_reports


def list_reports(reports, list_reports_with_status):
    """
    Return description of reports.

    The reports list is filtered and only public reports are provided. If the report is enabled in current
    configuration it will have (enabled) suffix (and (disabled) if it is disabled).
    """
    all_public_reports = [report for report in load_reports().values() if not is_report_internal(report)]
    all_public_reports = sorted(all_public_reports, key=lambda x: x.name)
    configured_reports = {x.name for x in reports.values()}
    available_reports = "Available reports:"
    for report in all_public_reports:
        status = "enabled" if report.name in configured_reports else "disabled"
        if list_reports_with_status != "default" and list_reports_with_status != status.upper():
            continue
        if not is_report_default(report):
            status += " - non-default"
        available_reports += f"\n{report.name:20} - {report.description} ({status})"
    available_reports += (
        "\n\nEnable report by passing report name using --reports option. "
        "Use `all` to enable all default reports. "
        "Non-default reports can be only enabled using report name."
    )
    return available_reports


def load_reports_result_from_cache():
    cache_dir = get_robocop_cache_directory(ensure_exists=False)
    cache_file = cache_dir / ROBOCOP_CACHE_FILE
    if not cache_file.is_file():
        return None
    with open(cache_file) as fp:
        try:
            return json.load(fp)
        except json.JSONDecodeError:
            return None


def save_reports_result_to_cache(working_dir: str, report_results: dict):
    """
    Save results from Robocop reports to json file.

    Result file contains results grouped using working directory.
    That's why we are loading previous results and overwriting only
    the results for current working directory.
    """
    cache_dir = get_robocop_cache_directory(ensure_exists=True)
    cache_file = cache_dir / ROBOCOP_CACHE_FILE
    prev_results = load_reports_result_from_cache()
    if prev_results is None:
        prev_results = {}
    prev_results[working_dir] = report_results
    with open(cache_file, "w") as fp:
        json_string = json.dumps(prev_results, indent=4)
        fp.write(json_string)
