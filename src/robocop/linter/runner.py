from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, NoReturn

import typer
from robot.api import get_init_model, get_model, get_resource_model
from robot.errors import DataError

from robocop import exceptions
from robocop.cache import restore_diagnostics
from robocop.linter import reports
from robocop.linter.diagnostics import Diagnostics, RunStatistic
from robocop.linter.fix import FixApplier
from robocop.linter.reports import save_reports_result_to_cache
from robocop.linter.rules import FixableRule
from robocop.linter.utils.disablers import DisablersFinder
from robocop.linter.utils.file_types import get_resource_with_lang
from robocop.linter.utils.misc import is_suite_templated
from robocop.source_file import SourceFile, VirtualSourceFile

if TYPE_CHECKING:
    from robot.parsing import File

    from robocop.config import Config
    from robocop.config_manager import ConfigManager
    from robocop.linter.diagnostics import Diagnostic


class RobocopLinter:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.current_model: File = None
        self.reports: dict[str, reports.Report] = reports.get_reports(self.config_manager.default_config)
        self.diagnostics: list[Diagnostic] = []
        self.configure_reports()

    def get_model_for_file_type(self, source: Path, language: list[str] | None) -> File:
        """Recognize model type of the file and load the model."""
        # TODO: decide to migrate file type recognition based on imports from robocop
        if "__init__" in source.name:
            return get_resource_with_lang(get_init_model, source, language)
        if source.suffix == ".resource":
            return get_resource_with_lang(get_resource_model, source, language)
        return get_resource_with_lang(get_model, source, language)

    def get_cached_diagnostics(self, config: Config, source: Path) -> list[Diagnostic] | None:
        """
        Return cached diagnostics if available.

        Returns:
            List of cached diagnostics or None if no cache is available.

        """
        if not config.cache.enabled:
            return None
        cached_entry = self.config_manager.cache.get_linter_entry(source, config.hash())

        if cached_entry is not None:
            return restore_diagnostics(cached_entry, source, config)
        return None

    def get_model_diagnostics(self, source_file: SourceFile, fix_applier: FixApplier) -> list[Diagnostic] | None:
        """
        Run all selected rules on the model and return list of diagnostics.

        Returns:
            List of diagnostics or None if file cannot be decoded.

        """
        try:
            return self.run_check(source_file, fix_applier)
        except DataError as error:
            if not source_file.config.silent:
                print(f"Failed to decode {source_file.path} with an error: {error}. Skipping file")
            return None

    def run(self) -> list[Diagnostic]:
        """
        Run the diagnostic checks on the configured files and returns detected issues.

        This method iterates through the configured file paths and attempts to check
        each file for diagnostics. It processes files based on their types and uses
        the configuration provided for each file. The diagnostics for each file are
        aggregated, and a final report is generated. If configured, the diagnostics
        are returned; otherwise, the process exits with a suitable code based on the
        number of issues found.

        Returns:
            list[Diagnostic]: A list of detected issues in the analyzed files if the
            linter is configured to return results; otherwise, the function returns
            with an exit code based on the number of issues detected.

        Raises:
            DataError: Raised when a file cannot be decoded appropriately based on its
            configuration language.

        """
        self.diagnostics: list[Diagnostic] = []
        files = 0
        cached_files = 0
        fix_applier = FixApplier()
        for source_file in self.config_manager.paths:
            if source_file.config.verbose:
                print(f"Scanning file: {source_file.path}")
            diagnostics = self.get_cached_diagnostics(source_file.config, source_file.path)
            if diagnostics is not None:
                fixes = [diag.fix(source_file) for diag in diagnostics if isinstance(diag.rule, FixableRule)]
                if not fix_applier.apply_fixes(source_file, fixes):
                    self.diagnostics.extend(diagnostics)
                    files += 1
                    cached_files += 1
                    continue
            diagnostics = self.get_model_diagnostics(source_file, fix_applier)
            if diagnostics is None:
                continue
            self.diagnostics.extend(diagnostics)
            files += 1
            self.config_manager.cache.set_linter_entry(source_file.path, source_file.config.hash(), diagnostics)
        self.config_manager.cache.save()

        if not files and not self.config_manager.default_config.silent:
            print("No Robot files were found with the existing configuration.")
        if self.config_manager.default_config.verbose and cached_files > 0:
            print(f"Used cached results for {cached_files} of {files} files.")
        run_stats = RunStatistic(
            files_count=files, fix_stats=fix_applier.fix_stats, modified_files=fix_applier.modified_files
        )
        self.make_reports(run_stats=run_stats)
        if self.config_manager.default_config.linter.return_result:
            return self.diagnostics
        return self.return_with_exit_code(len(self.diagnostics))

    def run_check(self, source_file: SourceFile, fix_applier: FixApplier = None) -> list[Diagnostic]:
        """
        Run all rules on file model and return list of diagnostics.

        Args:
            source_file: SourceFile representing robot source file under the check.
            fix_applier: The applier responsible for applying fixes to the source file.

        """
        if fix_applier is None:
            fix_applier = FixApplier()
        templated = is_suite_templated(source_file.model)
        prev_fixable = 0
        # Iteratively scans, filters, applies fixes, and reloads model until convergence or no fixes remain
        for _ in range(20):
            found_diagnostics = []
            disablers = DisablersFinder(source_file.model)
            for checker in source_file.config.linter.checkers:
                found_diagnostics += [
                    diagnostic
                    for diagnostic in checker.scan_file(source_file, templated)
                    if not (
                        diagnostic.severity < source_file.config.linter.threshold
                        or disablers.is_rule_disabled(diagnostic)
                    )
                ]
                if disablers.file_disabled and found_diagnostics:  # special case to not report disabler as not used
                    return []
            for checker in source_file.config.linter.after_run_checkers:
                found_diagnostics += [
                    diagnostic
                    for diagnostic in checker.scan_file(source_file, disablers=disablers)
                    if not (
                        diagnostic.severity < source_file.config.linter.threshold
                        or disablers.is_rule_disabled(diagnostic)
                    )
                ]
            if found_diagnostics and source_file.config.linter.per_file_ignores:
                for ignored_file, ignored_rules in source_file.config.linter.per_file_ignores.items():
                    if source_file.path.match(ignored_file):
                        found_diagnostics = [
                            diagnostic
                            for diagnostic in found_diagnostics
                            if diagnostic.rule.rule_id not in ignored_rules
                            and diagnostic.rule.name not in ignored_rules
                        ]
            if not found_diagnostics or not (source_file.config.linter.fix or source_file.config.linter.diff):
                fix_applier.fix_stats.total_fixes += prev_fixable
                break
            fixable_diagnostics = [diag for diag in found_diagnostics if isinstance(diag.rule, FixableRule)]
            fix_applier.fix_stats.total_fixes += max(prev_fixable - len(fixable_diagnostics), 0)
            prev_fixable = len(fixable_diagnostics)
            # Collect fixes from diagnostics
            fixes = [diag.fix(source_file) for diag in fixable_diagnostics]
            if not fix_applier.apply_fixes(source_file, fixes):
                break
        if source_file.config.linter.fix and not source_file.config.linter.diff:
            source_file.write_changes()
        return found_diagnostics

    def run_project_checks(self) -> list[Diagnostic]:
        self.diagnostics: list[Diagnostic] = []
        config = self.config_manager.default_config
        project_name = self.config_manager.root.name
        project_source_file = VirtualSourceFile(Path(project_name), self.config_manager.default_config)
        for checker in config.linter.project_checkers:
            checker.issues = []
            checker.scan_project(project_source_file, self.config_manager)
            self.diagnostics.extend(
                [diagnostic for diagnostic in checker.issues if not (diagnostic.severity < config.linter.threshold)]
            )
        self.make_reports(run_stats=None)
        if config.linter.return_result:
            return self.diagnostics
        return self.return_with_exit_code(len(self.diagnostics))

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
            exit_code = self.reports["return_status"].return_status
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
                raise exceptions.InvalidConfigurationFormatError(config) from None
            if name not in self.reports:
                continue
            if param == "enabled":
                if value.lower() == "false":
                    del self.reports[name]
            else:
                self.reports[name].configure(param, value)

    def make_reports(self, run_stats: RunStatistic | None) -> None:
        report_results = {}
        prev_results = reports.load_reports_result_from_cache()
        prev_results = prev_results.get(str(self.config_manager.root)) if prev_results is not None else None
        is_persistent = self.config_manager.default_config.linter.persistent
        diagnostics = Diagnostics(self.diagnostics)
        for report in self.reports.values():
            prev_result = prev_results.get(report.name) if prev_results is not None else None
            report.generate_report(
                diagnostics=diagnostics,
                config_manager=self.config_manager,
                prev_results=prev_result,
                run_stats=run_stats,
            )
            if is_persistent and isinstance(report, reports.ComparableReport):
                result = report.persist_result()
                if result is not None:
                    report_results[report.name] = result
        if is_persistent:
            save_reports_result_to_cache(str(self.config_manager.root), report_results)
