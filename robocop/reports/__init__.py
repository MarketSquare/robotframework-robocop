"""
Reports are configurable summaries after Robocop scan. For example, it can be a total number of issues discovered.
They are dynamically loaded during setup according to a configuration.

Each report class collects rules messages from linter and parses it. At the end of the scan it will print the report.

To enable report use ``-r`` / ``--reports`` argument and the name of the report.
You can use separate arguments (``-r report1 -r report2``) or comma-separated list (``-r report1,report2``). Example::

    robocop --reports rules_by_id,some_other_report path/to/file.robot

To enable all default reports use ``--reports all``.  Non-default reports can be only enabled using report name.

The order of the reports is preserved. For example, if you want ``timestamp`` report to be printed before any
other reports, you can use following configuration::

    robocop --reports timestamp,all src.robot

Print list of all reports with their configured status by using ``--list-reports``::

    robocop --reports all --list-reports

You can filter the list using optional ENABLED/DISABLED argument::

    robocop --reports timestamp,sarif --list-reports DISABLED

"""
import inspect
from collections import OrderedDict

import robocop.exceptions
from robocop.utils.misc import modules_in_current_dir


class Report:
    """
    Base class for report class.
    Override `configure` method if you want to allow report configuration.
    Override `add_message`` if your report processes the Robocop issues.

    Set class attribute `DEFAULT` to `False` if you don't want your report to be included in `all` reports.
    """

    DEFAULT = True
    INTERNAL = False

    def configure(self, name, value):
        raise robocop.exceptions.ConfigGeneralError(
            f"Provided param '{name}' for report '{getattr(self, 'name')}' does not exist"
        )  # noqa

    def add_message(self, *args):
        pass


def load_reports():
    """
    Load all valid reports.
    Report is considered valid if it inherits from `Report` class
    and contains both `name` and `description` attributes.
    """
    reports = {}
    for module in modules_in_current_dir(__file__, __name__):
        classes = inspect.getmembers(module, inspect.isclass)
        for report_class in classes:
            if not issubclass(report_class[1], Report):
                continue
            report = report_class[1]()
            if not hasattr(report, "name") or not hasattr(report, "description"):
                continue
            reports[report.name] = report
    return reports


def is_report_default(report):
    return getattr(report, "DEFAULT", False)


def is_report_internal(report):
    return getattr(report, "INTERNAL", False)


def get_reports(configured_reports):
    """
    Returns dictionary with list of valid, enabled reports (listed in `configured_reports` set of str).
    If `configured_reports` contains `all` then all default reports are enabled.
    """
    reports = load_reports()
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
    """Returns description of reports.

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
