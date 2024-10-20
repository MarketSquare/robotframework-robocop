"""
Main class of Robocop module. Gathers files to be scanned, checkers, parses CLI arguments and scans files.
"""

import os
import sys
from collections import Counter
from typing import List

from robot.api import get_resource_model
from robot.errors import DataError

import robocop.exceptions
from robocop import checkers, reports
from robocop.config import Config
from robocop.files import get_files
from robocop.reports import is_report_comparable, load_reports_result_from_cache, save_reports_result_to_cache
from robocop.rules import Message, RuleFilter
from robocop.utils import DisablersFinder, FileType, FileTypeChecker, is_suite_templated
from robocop.utils.file_types import check_model_type, get_resource_with_lang
from robocop.utils.misc import ROBOCOP_RULES_URL, get_plural_form


class Robocop:
    """
    Main class for running the checks.

    If you want to run checks with non default configuration create your own ``Config`` and pass it to ``Robocop``.
    Use ``Robocop.run()`` method to start analysis. If ``from_cli`` is set to ``False`` it will return
    list of found issues in JSON format.

    Example::

        import robocop
        from robocop.config import Config

        config = Config()
        config.include = {'1003'}
        config.paths = ['tests\\atest\\rules\\section-out-of-order']

        robocop_runner = robocop.Robocop(config=config)
        issues = robocop_runner.run()

    """

    def __init__(self, from_cli: bool = False, config: Config = None):
        self.files = {}
        self.checkers = []
        self.rules = {}
        self.reports = {}
        self.root = os.getcwd()
        self.config = Config(from_cli=from_cli) if config is None else config
        self.from_cli = from_cli
        if not from_cli:
            self.config.reports.append("internal_json_report")
        self.out = self.set_output()

    def set_output(self):
        """Set output for printing to file if configured. Else use standard output"""
        return self.config.output or None

    def write_line(self, line):
        """Print line using file=self.out parameter (set in `set_output` method)"""
        print(line, file=self.out)

    def reload_config(self):
        """Reload checkers and reports based on current config"""
        self.load_checkers()
        self.config.reload(self.rules)
        self.load_reports()
        self.configure_checkers_or_reports()
        self.check_for_disabled_rules()
        self.list_checkers()

    def run(self):
        """Entry point for running scans"""
        self.reload_config()
        self.recognize_file_types()
        self.run_checks()
        self.make_reports()
        if self.config.output and not self.out.closed:
            self.out.close()
        if self.from_cli:
            sys.exit(self.reports["return_status"].return_status)
        else:
            return self.reports["internal_json_report"].issues

    def recognize_file_types(self):
        """
        Pre-parse files to recognize their types. If the filename is `__init__.*`, the type is `INIT`.
        Files with .resource extension are `RESOURCE` type.
        If the file is imported somewhere then file type is `RESOURCE`. Otherwise, file type is `GENERAL`.
        These types are important since they are used to define parsing class for robot API.
        """
        file_type_checker = FileTypeChecker(self.config.exec_dir)
        for file in get_files(self.config):
            if "__init__" in file.name:
                file_type = FileType.INIT
            elif file.suffix.lower() == ".resource":
                file_type = FileType.RESOURCE
            else:
                file_type = FileType.GENERAL
            file_type_checker.source = file
            try:
                resource_parser = file_type.get_parser()
                model = get_resource_with_lang(resource_parser, str(file), self.config.language)
                check_model_type(file_type_checker, model)
                self.files[file] = (file_type, model)
            except DataError:
                print(f"Failed to decode {file}. Default supported encoding by Robot Framework is UTF-8. Skipping file")

        for resource in file_type_checker.resource_files:
            if resource in self.files and self.files[resource][0].value != FileType.RESOURCE:
                self.files[resource] = (
                    FileType.RESOURCE,
                    get_resource_with_lang(get_resource_model, str(resource), self.config.language),
                )

    def run_checks(self):
        for file, file_model in self.files.items():
            if self.config.verbose:
                print(f"Scanning file: {file}")
            model = file_model[1]
            found_issues = self.run_check(model, str(file))
            found_issues.sort()
            for issue in found_issues:
                self.report(issue)
        found_issues = self.run_project_checks()
        for issue in found_issues:
            self.report(issue)
        if "file_stats" in self.reports:
            self.reports["file_stats"].files_count = len(self.files)

    def run_check(self, ast_model, filename, source=None):
        disablers = DisablersFinder(ast_model)
        if disablers.file_disabled:
            return []
        found_issues = []
        templated = is_suite_templated(ast_model)
        for checker in self.checkers:
            if checker.disabled:
                continue
            found_issues += [
                issue
                for issue in checker.scan_file(ast_model, filename, source, templated)
                if not disablers.is_rule_disabled(issue) and not issue.severity < self.config.threshold
            ]
        return found_issues

    def run_project_checks(self) -> List:
        found_issues = []
        for checker in self.checkers:
            if not checker.disabled and isinstance(checker, checkers.ProjectChecker):
                found_issues += [
                    issue for issue in checker.scan_project() if not issue.severity < self.config.threshold
                ]
        return sorted(found_issues)

    def report(self, rule_msg: Message):
        for report in self.reports.values():
            report.add_message(rule_msg)
        try:
            source_rel = os.path.relpath(os.path.expanduser(rule_msg.source), self.root)
        except ValueError:
            source_rel = rule_msg.source
        self.log_message(
            source=rule_msg.source,
            source_rel=source_rel,
            line=rule_msg.line,
            col=rule_msg.col,
            end_line=rule_msg.end_line,
            end_col=rule_msg.end_col,
            severity=rule_msg.severity.value,
            rule_id=rule_msg.rule_id,
            desc=rule_msg.desc,
            name=rule_msg.name,
        )

    def log_message(self, **kwargs):
        self.write_line(self.config.format.format(**kwargs))

    def load_checkers(self):
        self.checkers = []
        self.rules = {}
        checkers.init(self)

    def list_checkers(self):
        if not (self.config.list or self.config.list_configurables):
            return
        if self.config.list_configurables:
            print(
                "All rules have configurable parameter 'severity'. Allowed values are:"
                "\n    E / error\n    W / warning\n    I / info\n"
            )
        pattern = self.config.list if self.config.list else self.config.list_configurables
        rule_by_id = RuleFilter().get_filtered_rules(self.rules, pattern)
        severity_counter = Counter({"E": 0, "W": 0, "I": 0})
        for rule in rule_by_id:
            if self.config.list:
                print(rule)
                severity_counter[rule.severity.value] += 1
            else:
                _, params = rule.available_configurables(include_severity=False)
                if params:
                    print(f"{rule}\n" f"    {params}")
                    severity_counter[rule.severity.value] += 1
        configurable_rules_sum = sum(severity_counter.values())
        plural = get_plural_form(configurable_rules_sum)
        print(
            f"\nAltogether {configurable_rules_sum} rule{plural} with following severity:\n"
            f"    {severity_counter['E']} error rule{get_plural_form(severity_counter['E'])},\n"
            f"    {severity_counter['W']} warning rule{get_plural_form(severity_counter['W'])},\n"
            f"    {severity_counter['I']} info rule{get_plural_form(severity_counter['I'])}.\n"
        )
        print(f"Visit {ROBOCOP_RULES_URL.format(version='stable')} page for detailed documentation.")
        sys.exit()

    def load_reports(self):
        self.reports = reports.get_reports(self.config.reports)
        if self.config.list_reports:
            available_reports = reports.list_reports(self.reports, self.config.list_reports)
            print(available_reports)
            sys.exit()

    def register_checker(self, checker):
        for rule_name, rule in checker.rules.items():
            self.rules[rule_name] = rule
            self.rules[rule.rule_id] = rule
        self.checkers.append(checker)

    def check_for_disabled_rules(self):
        """Check checker configuration to disable rules."""
        for checker in self.checkers:
            if not self.any_rule_enabled(checker):
                checker.disabled = True

    def make_reports(self):
        report_results = {}
        prev_results = load_reports_result_from_cache()
        prev_results = prev_results.get(str(self.root)) if prev_results is not None else None
        for report in self.reports.values():
            if report.name == "sarif":
                output = report.get_report(self.config, self.rules)
            elif is_report_comparable(report):
                prev_result = prev_results.get(report.name) if prev_results is not None else None
                output = report.get_report(prev_result)
            else:
                output = report.get_report()
            if output is not None:
                self.write_line(output)
            if self.config.persistent and is_report_comparable(report):
                result = report.persist_result()
                if result is not None:
                    report_results[report.name] = result
        if self.config.persistent:
            save_reports_result_to_cache(str(self.root), report_results)

    def any_rule_enabled(self, checker) -> bool:
        for name, rule in checker.rules.items():
            rule.enabled = self.config.is_rule_enabled(rule)
            checker.rules[name] = rule
        return any(msg.enabled for msg in checker.rules.values())

    def configure_checkers_or_reports(self):
        for config in self.config.configure:
            if config.count(":") < 2:
                raise robocop.exceptions.ConfigGeneralError(
                    f"Provided invalid config: '{config}' (general pattern: <rule>:<param>:<value>)"
                ) from None
            rule_or_report, param, value = config.split(":", maxsplit=2)
            if rule_or_report in self.rules:
                rule = self.rules[rule_or_report]
                if rule.deprecated:
                    print(rule.deprecation_warning)
                else:
                    rule.configure(param, value)
            elif rule_or_report in self.reports:
                self.reports[rule_or_report].configure(param, value)
            else:
                raise robocop.exceptions.RuleOrReportDoesNotExist(rule_or_report, self.rules)


def run_robocop():
    try:
        linter = Robocop(from_cli=True)
        linter.run()
    except robocop.exceptions.RobotFrameworkParsingError:
        raise
    except robocop.exceptions.RobocopFatalError as err:
        print(f"Error: {err}")
        sys.exit(1)
    except Exception as err:
        message = (
            "\nFatal exception occurred. You can create an issue at "
            "https://github.com/MarketSquare/robotframework-robocop/issues/new/choose - Thanks!"
        )
        err.args = (err.args[0] + message,) + err.args[1:]
        raise err
