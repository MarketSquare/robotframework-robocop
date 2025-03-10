from __future__ import annotations

from typing import TYPE_CHECKING, NoReturn

import typer
from robot.api import get_init_model, get_model, get_resource_model
from robot.errors import DataError

from robocop.linter import exceptions, reports
from robocop.linter.reports import save_reports_result_to_cache
from robocop.linter.utils.disablers import DisablersFinder
from robocop.linter.utils.misc import is_suite_templated

if TYPE_CHECKING:
    from pathlib import Path

    from robot.parsing import File

    from robocop.config import Config, ConfigManager
    from robocop.linter.diagnostics import Diagnostic


class RobocopLinter:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.config: Config = self.config_manager.default_config
        self.current_model: File = None
        self.reports: dict[str, reports.Report] = reports.get_reports(self.config)
        self.diagnostics: list[Diagnostic] = []
        self.configure_reports()

    def get_model_for_file_type(self, source: Path) -> File:
        """Recognize model type of the file and load the model."""
        # TODO: decide to migrate file type recognition based on imports from robocop
        # TODO: language
        if "__init__" in source.name:
            return get_init_model(source)
        if source.suffix == ".resource":
            return get_resource_model(source)
        return get_model(source)

    def run(self) -> list[Diagnostic]:
        issues_no = 0
        files = 0
        for source, config in self.config_manager.paths:
            self.config = config
            if self.config.verbose:
                print(f"Scanning file: {source}")
            try:
                self.current_model = self.get_model_for_file_type(source)
            except DataError:
                print(
                    f"Failed to decode {source}. Default supported encoding by Robot Framework is UTF-8. Skipping file"
                )
                continue
            files += 1
            diagnostics = self.run_check(str(source))
            issues_no += len(diagnostics)
            for diagnostic in diagnostics:
                self.report(diagnostic)
            self.diagnostics.extend(diagnostics)
        if not files:
            print("No Robot files were found with the existing configuration.")
        if "file_stats" in self.reports:
            self.reports["file_stats"].files_count = files
        self.make_reports()
        if self.config_manager.default_config.linter.return_result:
            return self.diagnostics
        return self.return_with_exit_code(issues_no)

    def run_check(self, filename: str, source: str | None = None) -> list[Diagnostic]:
        disablers = DisablersFinder(self.current_model)
        if disablers.file_disabled:
            return []
        found_diagnostics = []
        templated = is_suite_templated(self.current_model)
        for checker in self.config.linter.checkers:
            if checker.disabled:
                continue
            found_diagnostics += [
                diagnostic
                for diagnostic in checker.scan_file(self.current_model, filename, source, templated)
                if not disablers.is_rule_disabled(diagnostic) and not diagnostic.severity < self.config.linter.threshold
            ]
        return found_diagnostics

    def return_with_exit_code(self, issues_count: int) -> NoReturn:
        """
        Exit the Robocop with exit code.

        Exit code is always 0 if --exit-zero is set. Otherwise, it can be calculated by optional `return_status`
        report. If it is not enabled, exit code will be:

        - 0 if no issues found
        - 1 if any issue found
        - 2 if Robocop terminated abnormally

        """
        if self.config_manager.default_config.linter.exit_zero:
            exit_code = 0
        elif "return_status" in self.reports:
            exit_code = self.reports["return_status"].exit_code
        else:
            exit_code = 1 if issues_count else 0
        raise typer.Exit(code=exit_code)

    def configure_reports(self):
        """Configure reports using default configuration only."""
        for config in self.config_manager.default_config.linter.configure:
            try:  # TODO custom parser to apply in linter/formatter/here
                name, param_and_value = config.split(".", maxsplit=1)
                param, value = param_and_value.split("=", maxsplit=1)
            except ValueError:
                raise exceptions.ConfigGeneralError(
                    f"Provided invalid config: '{config}' (general pattern: <rule/report>.<param>=<value>)"
                ) from None
            if name in self.reports:
                self.reports[name].configure(param, value)

    def report(self, diagnostic: Diagnostic) -> None:
        diagnostic.model = self.current_model  # TODO: Embed it into diagnostic where the report is raised
        for report in self.reports.values():
            report.add_message(diagnostic)

    def make_reports(self) -> None:
        report_results = {}
        prev_results = reports.load_reports_result_from_cache()
        prev_results = prev_results.get(str(self.config_manager.root)) if prev_results is not None else None
        is_persistent = self.config_manager.default_config.linter.persistent
        for report in self.reports.values():
            if report.name == "sarif":
                output = report.get_report(self.config_manager.root, self.rules)
            elif isinstance(report, reports.ComparableReport):  # TODO:
                prev_result = prev_results.get(report.name) if prev_results is not None else None
                output = report.get_report(prev_result)
            else:
                output = report.get_report()
            if output is not None:
                print(output)
            if is_persistent and isinstance(report, reports.ComparableReport):
                result = report.persist_result()
                if result is not None:
                    report_results[report.name] = result
        if is_persistent:
            save_reports_result_to_cache(str(self.config_manager.root), report_results)
