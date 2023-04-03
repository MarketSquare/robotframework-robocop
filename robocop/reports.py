"""
Reports are configurable summaries after Robocop scan. For example, it can be a total number of issues discovered.
They are dynamically loaded during setup according to a configuration.

Each report class collects rules messages from linter and parses it. At the end of the scan it will print the report.

To enable report use ``-r`` / ``--reports`` argument and the name of the report.
You can use separate arguments (``-r report1 -r report2``) or comma-separated list (``-r report1,report2``). Example::

    robocop --reports rules_by_id,some_other_report path/to/file.robot

To enable all default reports use ``--reports all``.

The order of the reports is preserved. For example, if you want ``timestamp`` report to be printed before any
other reports, you can use following configuration::

    robocop --reports timestamp,all src.robot

"""
import inspect
import json
import sys
from collections import OrderedDict, defaultdict
from datetime import datetime, timezone
from operator import itemgetter
from pathlib import Path
from timeit import default_timer as timer
from warnings import warn

import pytz

import robocop.exceptions
from robocop.rules import Message
from robocop.utils import RecommendationFinder
from robocop.version import __version__


class Report:
    """
    Base class for report class.
    Override `configure` method if you want to allow report configuration.
    Override `add_message`` if your report processes the Robocop issues.

    Set class attribute `DEFAULT` to `False` if you don't want your report to be included in `all` reports.
    """

    DEFAULT = True

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
    classes = inspect.getmembers(sys.modules[__name__], inspect.isclass)
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


def list_reports(reports):
    """Returns description of enabled reports."""
    sorted_by_name = sorted(reports.values(), key=lambda x: x.name)
    available_reports = "Available reports:\n"
    available_reports += "\n".join(f"{report.name:20} - {report.description}" for report in sorted_by_name) + "\n"
    available_reports += "all" + " " * 18 + "- Turns on all default reports"
    return available_reports


class RulesByIdReport(Report):
    """
    Report name: ``rules_by_id``

    Report that groups linter rules messages by rule id and prints it ordered by most common message.
    Example::

        Issues by ID:
        W0502 (too-little-calls-in-keyword) : 5
        W0201 (missing-doc-keyword)         : 4
        E0401 (parsing-error)               : 3
        W0301 (not-allowed-char-in-name)    : 2
        W0901 (keyword-after-return)        : 1
    """

    def __init__(self):
        self.name = "rules_by_id"
        self.description = "Groups detected issues by rule id and prints it ordered by most common"
        self.message_counter = defaultdict(int)

    def add_message(self, message: Message):  # noqa
        self.message_counter[message.get_fullname()] += 1

    def get_report(self) -> str:
        message_counter_ordered = sorted(self.message_counter.items(), key=itemgetter(1), reverse=True)
        report = "\nIssues by ID:\n"
        if not message_counter_ordered:
            report += "No issues found."
            return report
        longest_name = max(len(msg[0]) for msg in message_counter_ordered)
        report += "\n".join(f"{message:{longest_name}} : {count}" for message, count in message_counter_ordered)
        return report


class RulesBySeverityReport(Report):
    """
    Report name: ``rules_by_error_type``

    Report that groups linter rules messages by severity and prints total of issues per every severity level.

    Example::

        Found 15 issues: 4 ERRORs, 11 WARNINGs.
    """

    def __init__(self):
        self.name = "rules_by_error_type"
        self.description = "Prints total number of issues grouped by severity"
        self.severity_counter = defaultdict(int)

    def add_message(self, message: Message):
        self.severity_counter[message.severity] += 1

    def get_report(self) -> str:
        issues_count = sum(self.severity_counter.values())
        if not issues_count:
            return "\nFound 0 issues."

        report = "\nFound 1 issue: " if issues_count == 1 else f"\nFound {issues_count} issues: "
        warning_types = []
        for severity, count in self.severity_counter.items():
            plural = "" if count == 1 else "s"
            warning_types.append(f"{count} {severity.name}{plural}")
        report += ", ".join(warning_types)
        report += "."
        return report


class ReturnStatusReport(Report):
    """
    Report name: ``return_status``

    This report is always enabled.
    Report that checks if number of returned rules messages for given severity value does not exceed preset threshold.
    That information is later used as a return status from Robocop.
    """

    def __init__(self):
        self.name = "return_status"
        self.description = "Checks if number of specific issues exceed quality gate limits"
        self.return_status = 0
        self.counter = RulesBySeverityReport()
        self.quality_gate = {"E": 0, "W": 0, "I": -1}

    def configure(self, name, value):
        if name not in ["quality_gate", "quality_gates"]:
            super().configure(name, value)
        for val in value.split(":"):
            try:
                name, count = val.split("=", maxsplit=1)
                if name.upper() in self.quality_gate:
                    self.quality_gate[name.upper()] = int(count)
            except ValueError:
                continue

    def add_message(self, message: Message):
        self.counter.add_message(message)

    def get_report(self):
        for severity, count in self.counter.severity_counter.items():
            threshold = self.quality_gate.get(severity.value, 0)
            if -1 < threshold < count:
                self.return_status += count - threshold
        self.return_status = min(self.return_status, 255)


class TimeTakenReport(Report):
    """
    Report name: ``scan_timer``

    Report that returns Robocop execution time

    Example::

        Scan finished in 0.054s.
    """

    def __init__(self):
        self.name = "scan_timer"
        self.description = "Returns Robocop execution time"
        self.start_time = timer()

    def get_report(self) -> str:
        return f"\nScan finished in {timer() - self.start_time:.3f}s."


class JsonReport(Report):
    """
    Report name: ``json_report``

    Report that returns list of found issues in JSON format.
    """

    DEFAULT = False

    def __init__(self):
        self.name = "json_report"
        self.description = "Accumulates found issues in JSON format"
        self.issues = []

    def add_message(self, message: Message):
        self.issues.append(message.to_json())

    def get_report(self):
        return None


class FileStatsReport(Report):
    """
    Report name: ``file_stats``

    Report that displays overall statistics about number of processed files.

    Example::

        Processed 7 files from which 5 files contained issues.
    """

    def __init__(self):
        self.name = "file_stats"
        self.description = "Prints overall statistics about number of processed files"
        self.files_count = 0
        self.files_with_issues = set()

    def add_message(self, message: Message):
        self.files_with_issues.add(message.source)

    def get_report(self) -> str:
        if not self.files_count:
            return "\nNo files were processed."
        plural_files = "s" if self.files_count > 1 else ""
        if not self.files_with_issues:
            return f"\nProcessed {self.files_count} file{plural_files} but no issues were found."

        plural_files_with_issues = "" if len(self.files_with_issues) == 1 else "s"
        return (
            f"\nProcessed {self.files_count} file{plural_files} from which {len(self.files_with_issues)} "
            f"file{plural_files_with_issues} contained issues."
        )


class RobocopVersionReport(Report):
    """
    Report name: ``version``

    Report that returns Robocop version.

    Example::

        Report generated by Robocop version: 2.0.2
    """

    def __init__(self):
        self.name = "version"
        self.description = "Returns Robocop version"

    def get_report(self) -> str:
        return f"\nReport generated by Robocop version: {__version__}"


class TimestampReport(Report):
    """
    Report name: ``timestamp``

    Report that returns Robocop execution timestamp.
    Timestamp follows local time in format of
    `Year-Month-Day Hours(24-hour clock):Minutes:Seconds ±hh:mm UTC offset` as default.

    Example::

        Reported: 2022-07-10 21:25:00 +0300

    Both of default values, ``timezone`` and ``format`` can be configured by
    ``-c/--configure`` and ``timestamp:timezone:"<timezone name>"`` and/or ``timestamp:format:"<format string>"``::

        robocop --configure timestamp:timezone:"Europe/Paris" --configure timestamp:format:"%Y-%m-%d %H:%M:%S %Z %z"

    This yields following timestamp report::

         Reported: 2022-07-10 20:38:10 CEST +0200

    For timezone names,
    see: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

    For timestamp formats,
    see: https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes

    Useful configurations::

        Local time to ISO 8601 format:
        robocop --configure timestamp:format:"%Y-%m-%dT%H:%M:%S%z"

        UTC time:
        robocop --configure timestamp:timezone:"UTC" --configure timestamp:format:"%Y-%m-%dT%H:%M:%S %Z %z"

        Timestamp with high precision:
        robocop --configure timestamp:format:"%Y-%m-%dT%H:%M:%S.%f %z"

        12-hour clock:
        robocop --configure timestamp:format:"%Y-%m-%d %I:%M:%S %p %Z %z"

        More human readable format 'On 10 July 2022 07:26:24 +0300':
        robocop --configure timestamp:format:"On %d %B %Y %H:%M:%S %z"

    """

    def __init__(self):
        self.name = "timestamp"
        self.description = "Returns Robocop execution timestamp."
        self.timezone = "local"
        self.format = "%Y-%m-%d %H:%M:%S %z"

    def configure(self, name, value):
        if name == "timezone":
            self.timezone = value
        elif name == "format":
            if value:
                self.format = value
            else:
                warn("Empty format string for `timestamp` report does not make sense. Default format used.")
        else:
            super().configure(name, value)

    def get_report(self) -> str:
        return f"\nReported: {self._get_timestamp()}"

    def _get_timestamp(self) -> str:
        try:
            if self.timezone == "local":
                timezone_code = datetime.now(timezone.utc).astimezone().tzinfo
            else:
                timezone_code = pytz.timezone(self.timezone)
            return datetime.now(timezone_code).strftime(self.format)
        except pytz.exceptions.UnknownTimeZoneError as err:
            raise robocop.exceptions.ConfigGeneralError(
                f"Provided timezone '{self.timezone}' for report '{getattr(self, 'name')}' is not valid. "
                "Use timezone names like `Europe\\Helsinki`."
                "See: https://en.wikipedia.org/wiki/List_of_tz_database_time_zone"
            ) from err  # noqa


class SarifReport(Report):
    """
    Report name: ``sarif``

    Report that generates SARIF output file.

    This report is not included in the default reports. The ``--reports all`` option will not enable this report.
    You can still enable it using report name directly: ``--reports sarif`` or ``--reports all,sarif``.

    All fields required by GitHub Code Scanning are supported. The output file will be generated
    in the current working directory with the ``.sarif.json`` name.

    You can configure output directory and report filename::

        robocop --configure sarif:output_dir:C:/sarif_reports --configure sarif:report_filename:.sarif

    """

    DEFAULT = False
    SCHEMA_VERSION = "2.1.0"
    SCHEMA = f"https://json.schemastore.org/sarif-{SCHEMA_VERSION}.json"

    def __init__(self):
        self.name = "sarif"
        self.description = "Generate SARIF output file"
        self.output_dir = None
        self.report_filename = ".sarif.json"
        self.issues = []

    def configure(self, name, value):
        if name == "output_dir":
            self.output_dir = Path(value)
            self.output_dir.mkdir(parents=True, exist_ok=True)
        elif name == "report_filename":
            self.report_filename = value
        else:
            super().configure(name, value)

    @staticmethod
    def map_severity_to_level(severity):
        return {"WARNING": "warning", "ERROR": "error", "INFO": "note"}[severity.name]

    def get_rule_desc(self, rule):
        return {
            "id": rule.rule_id,
            "name": rule.name,
            "helpUri": f"https://robocop.readthedocs.io/en/stable/rules.html#{rule.name}",
            "shortDescription": {"text": rule.msg},
            "fullDescription": {"text": rule.docs},
            "defaultConfiguration": {"level": self.map_severity_to_level(rule.default_severity)},
            "help": {"text": rule.docs, "markdown": rule.docs},
        }

    def add_message(self, message: Message):
        self.issues.append(message)

    def generate_sarif_issues(self, config):
        sarif_issues = []
        for issue in self.issues:
            relative_uri = Path(issue.source).relative_to(config.root)
            sarif_issue = {
                "ruleId": issue.rule_id,
                "level": self.map_severity_to_level(issue.severity),
                "message": {"text": issue.desc},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": relative_uri.as_posix(), "uriBaseId": "%SRCROOT%"},
                            "region": {
                                "startLine": issue.line,
                                "endLine": issue.end_line,
                                "startColumn": issue.col,
                                "endColumn": issue.end_col,
                            },
                        }
                    }
                ],
            }
            sarif_issues.append(sarif_issue)
        return sarif_issues

    def generate_rules_config(self, rules):
        unique_enabled_rules = {rule.rule_id: rule for rule in rules.values() if rule.enabled}
        sorted_rules = sorted(unique_enabled_rules.values(), key=lambda x: x.rule_id)
        rules_config = [self.get_rule_desc(rule) for rule in sorted_rules]
        return rules_config

    def generate_sarif_report(self, config, rules):
        report = {
            "$schema": self.SCHEMA,
            "version": self.SCHEMA_VERSION,
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "Robocop",
                            "semanticVersion": __version__,
                            "informationUri": "https://robocop.readthedocs.io/",
                            "rules": self.generate_rules_config(rules),
                        }
                    },
                    "automationDetails": {"id": "robocop/"},
                    "results": self.generate_sarif_issues(config),
                }
            ],
        }
        return report

    def get_report(self, config, rules) -> str:
        report = self.generate_sarif_report(config, rules)
        if self.output_dir is not None:
            output_path = self.output_dir / self.report_filename
        else:
            output_path = Path(self.report_filename)
        with open(output_path, "w") as fp:
            json_string = json.dumps(report, indent=4)
            fp.write(json_string)
        return f"Generated SARIF report in {output_path}"
