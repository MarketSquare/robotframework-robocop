from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING, NoReturn

import typer
from robot.api import get_init_model, get_model, get_resource_model
from robot.errors import DataError

from robocop import exceptions
from robocop.cache import restore_diagnostics
from robocop.files import resolve_path
from robocop.linter import reports
from robocop.linter.diagnostics import Diagnostics, RunStatistic
from robocop.linter.fix import FixApplier
from robocop.linter.reports import save_reports_result_to_cache
from robocop.linter.utils.disablers import DisablersFinder
from robocop.linter.utils.file_types import get_resource_with_lang
from robocop.linter.utils.misc import is_suite_templated
from robocop.project.context import build_project_context
from robocop.runtime.resolver import ConfigResolver
from robocop.source_file import SourceFile, VirtualSourceFile

if TYPE_CHECKING:
    from robot.parsing import File

    from robocop.config.manager import ConfigManager
    from robocop.config.schema import Config
    from robocop.linter.diagnostics import Diagnostic
    from robocop.linter.rules import ProjectChecker
    from robocop.project.context import ProjectContext


class RobocopLinter:
    def __init__(self, config_manager: ConfigManager) -> None:
        self.config_manager = config_manager
        self.config_resolver = ConfigResolver(load_rules=True)
        self.current_model: File = None
        # TODO: we can move reports to config resolver
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
        cached_entry = self.config_manager.cache.get_linter_entry(source, config.hash)

        if cached_entry is not None:
            resolved_config = self.config_resolver.resolve_config(config)
            return restore_diagnostics(cached_entry, source, config, resolved_config)
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
        self.diagnostics = []
        files = 0
        cached_files = 0
        checked_paths: set[Path] = set()
        fix_applier = FixApplier()
        for source_file in self.config_manager.paths:
            if source_file.config.verbose:
                print(f"Scanning file: {source_file.path}")
            checked_paths.add(source_file.resolved_path)
            diagnostics = self.get_cached_diagnostics(source_file.config, source_file.path)
            if diagnostics is not None:
                no_fixables = all(not diag.rule.fixable for diag in diagnostics)
                if no_fixables or not (source_file.config.linter.fix or source_file.config.linter.diff):
                    self.diagnostics.extend(diagnostics)
                    files += 1
                    cached_files += 1
                    continue
            diagnostics = self.get_model_diagnostics(source_file, fix_applier)
            if diagnostics is None:
                continue
            self.diagnostics.extend(diagnostics)
            files += 1
            if not source_file.config.linter.diff:  # diff simulate fixes, so it's best to ignore the results
                self.config_manager.cache.set_linter_entry(source_file.path, source_file.config.hash, diagnostics)
        self.config_manager.cache.save()
        self.diagnostics.extend(self.run_project_checks(fix_applier, checked_paths))
        self.config_manager.cache.save()  # project analysis may cache imported libraries

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

    def run_check(self, source_file: SourceFile, fix_applier: FixApplier | None = None) -> list[Diagnostic]:
        """
        Run all rules on file model and return list of diagnostics.

        Args:
            source_file: SourceFile representing robot source file under the check.
            fix_applier: The applier responsible for applying fixes to the source file.

        """
        resolved_config = self.config_resolver.resolve_config(source_file.config)
        if fix_applier is None:
            fix_applier = FixApplier()
        templated = is_suite_templated(source_file.model)
        prev_fixable = 0
        # Iteratively scans, filters, applies fixes, and reloads model until convergence or no fixes remain
        for _ in range(20):
            found_diagnostics = []
            disablers = DisablersFinder(source_file.model)
            for checker in resolved_config.checkers:
                found_diagnostics += [
                    diagnostic
                    for diagnostic in checker.scan_file(source_file, templated)  # type: ignore[attr-defined]
                    if not (
                        diagnostic.severity < source_file.config.linter.threshold
                        or disablers.is_rule_disabled(diagnostic)
                    )
                ]
                if disablers.file_disabled and found_diagnostics:  # special case to not report disabler as not used
                    return []
            for checker in resolved_config.after_run_checkers:
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
            fixable_diagnostics = [diag for diag in found_diagnostics if diag.rule.fixable]
            fix_applier.fix_stats.total_fixes += max(prev_fixable - len(fixable_diagnostics), 0)
            prev_fixable = len(fixable_diagnostics)
            # Collect fixes from diagnostics
            fixes = [diag.fix or diag.rule.fix(diag, source_file.source_lines) for diag in fixable_diagnostics]
            if not fix_applier.apply_fixes(source_file, [fix for fix in fixes if fix]):
                break
        if source_file.config.linter.fix and not source_file.config.linter.diff:
            source_file.write_changes()
        return found_diagnostics

    def run_project_checks(
        self, fix_applier: FixApplier | None = None, checked_paths: set[Path] | None = None
    ) -> list[Diagnostic]:
        """
        Run project level checkers on the whole project.

        Project checkers are only run if the project analysis is enabled. By default it happens whenever
        at least one project rule is enabled. It can be forced or disabled with the ``project`` option.

        Args:
            fix_applier: The applier responsible for applying fixes to the source files. Project checks are
                repeated after applying the fixes, so that the reported issues match the fixed files.
            checked_paths: Paths of the files selected for the run. Only those files can be fixed, even though
                the project context is built from the whole project.

        Returns:
            List of diagnostics found by the project checkers.

        """
        config = self.config_manager.default_config
        if config.project is False:
            return []
        resolved_config = self.config_resolver.resolve_config(config)
        if not resolved_config.project_checkers:
            return []
        if fix_applier is None:
            fix_applier = FixApplier()
        project_name = self.config_manager.root.name
        project_source_file = VirtualSourceFile(Path(project_name), config)
        diagnostics = self.scan_project(project_source_file, resolved_config.project_checkers, config)
        if not (config.linter.fix or config.linter.diff):
            return diagnostics
        # Fixes may reveal or resolve other issues, so the project is scanned again until it converges.
        # In the diff mode files are not saved, so repeating the analysis would produce the same diagnostics.
        attempts = 5 if config.linter.fix and not config.linter.diff else 1
        for _ in range(attempts):
            if not self.apply_project_fixes(diagnostics, fix_applier, checked_paths, save=not config.linter.diff):
                break
            diagnostics = self.scan_project(project_source_file, resolved_config.project_checkers, config)
        return diagnostics

    def scan_project(
        self,
        project_source_file: VirtualSourceFile,
        project_checkers: list[ProjectChecker],
        config: Config,
    ) -> list[Diagnostic]:
        """
        Build the project context and run every project checker on it.

        Returns:
            List of diagnostics found by the project checkers.

        """
        context = self.build_context(config)
        diagnostics: list[Diagnostic] = []
        for checker in project_checkers:
            checker.issues = []
            checker.scan_project(project_source_file, self.config_manager, context)
            diagnostics.extend(
                [diagnostic for diagnostic in checker.issues if not (diagnostic.severity < config.linter.threshold)]
            )
        return diagnostics

    def apply_project_fixes(
        self,
        diagnostics: list[Diagnostic],
        fix_applier: FixApplier,
        checked_paths: set[Path] | None,
        save: bool,
    ) -> bool:
        """
        Apply fixes for the issues reported by the project checkers.

        Diagnostics reported by project checkers point to different source files, so they are grouped by the file
        first. Every file is fixed and saved separately. Only files selected for the run are fixed - the project
        context contains every file from the project, but files the user did not select are never modified.

        Args:
            diagnostics: Diagnostics reported by the project checkers.
            fix_applier: The applier responsible for applying fixes to the source files.
            checked_paths: Paths of the files selected for the run. If None, all files can be fixed.
            save: Whether the fixed files should be saved. Disabled in the diff mode.

        Returns:
            True if any fix was applied.

        """
        diag_by_source: dict[Path, list[Diagnostic]] = defaultdict(list)
        for diagnostic in diagnostics:
            if not diagnostic.rule.fixable:
                continue
            if checked_paths is not None and diagnostic.source.resolved_path not in checked_paths:
                continue
            diag_by_source[diagnostic.source.path].append(diagnostic)
        if not diag_by_source:
            return False
        modified_files = {source_file.resolved_path: source_file for source_file in fix_applier.modified_files}
        project_files = {source_file.resolved_path: source_file for source_file in self.config_manager.project_paths}
        fixed = False
        for path, source_diagnostics in diag_by_source.items():
            # reuse source file already parsed for the project context, so that the next scan sees fixed model
            resolved_path = resolve_path(path)
            source_file = modified_files.get(resolved_path) or project_files.get(resolved_path)
            if source_file is None:
                source_file = source_diagnostics[0].source
            fixes = [diag.fix or diag.rule.fix(diag, source_file.source_lines) for diag in source_diagnostics]
            fixes_before = self.count_applied_fixes(fix_applier)
            if not fix_applier.apply_fixes(source_file, [fix for fix in fixes if fix]):
                continue
            fix_applier.fix_stats.total_fixes += self.count_applied_fixes(fix_applier) - fixes_before
            fixed = True
            if save:
                source_file.write_changes()
        return fixed

    @staticmethod
    def count_applied_fixes(fix_applier: FixApplier) -> int:
        return sum(sum(rules.values()) for rules in fix_applier.fix_stats.by_file.values())

    def build_context(self, config: Config) -> ProjectContext:
        """
        Parse the whole project and build the context shared by all project checkers.

        Returns:
            ProjectContext with parsed files, keyword index and resolved imports.

        """
        context = build_project_context(self.config_manager, silent=config.silent)
        if config.verbose and not config.silent:
            print(f"Built project context from {len(context.files)} files.")
        return context

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
            exit_code = self.reports["return_status"].return_status  # type: ignore[attr-defined]
        else:
            exit_code = 1 if issues_count else 0
        raise typer.Exit(code=exit_code)

    def configure_reports(self) -> None:
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
                resolved_config=self.config_resolver.resolve_config(self.config_manager.default_config),
            )
            if is_persistent and isinstance(report, reports.ComparableReport):
                result = report.persist_result()
                if result is not None:
                    report_results[report.name] = result
        if is_persistent:
            save_reports_result_to_cache(str(self.config_manager.root), report_results)
