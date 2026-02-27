from __future__ import annotations

from typing import TYPE_CHECKING

import robocop.linter.reports
from robocop.linter.utils.misc import get_plural_form, get_string_diff

if TYPE_CHECKING:
    from robocop.config.schema import Config
    from robocop.linter.diagnostics import Diagnostic, Diagnostics


class FileStatsReport(robocop.linter.reports.ComparableReport):
    """
    **Report name**: ``file_stats``

    Report that displays overall statistics about the number of processed files.

    Example:
        Processed 7 files from which 5 files contained issues.

    """

    def __init__(self, config: Config) -> None:
        self.name = "file_stats"
        self.description = "Prints overall statistics about number of processed files"
        self.files_count = 0
        self.files_with_issues: dict[str, list[Diagnostic]] = {}
        super().__init__(config)

    def persist_result(self) -> dict[str, int]:
        return {"files_count": self.files_count, "files_with_issues": len(self.files_with_issues)}

    def generate_report(  # type: ignore[override]
        self,
        diagnostics: Diagnostics,
        prev_results: dict[str, int] | None = None,
        **kwargs: object,
    ) -> None:
        self.files_with_issues = diagnostics.diag_by_source
        if run_stats := kwargs.get("run_stats"):
            self.files_count = run_stats.files_count  # type: ignore[attr-defined]
        if self.compare_runs and prev_results:
            output = self.get_report_with_compare(prev_results)
        else:
            output = self.get_report_without_compare()
        if self.config.silent:
            return
        print(output)

    def get_report_with_compare(self, prev_results: dict[str, int]) -> str:
        plural_files = get_plural_form(self.files_count)
        prev_files_count = prev_results["files_count"]
        prev_files_with_issues = prev_results["files_with_issues"]
        if not self.files_count:
            if prev_files_count == 1:
                return "\nNo files were processed. Previously 1 file was processed."
            return f"\nNo files were processed. Previously {prev_files_count} files were processed."
        prev_count = f" ({get_string_diff(prev_files_count, self.files_count)})"
        processed_files_summary = f"\nProcessed {self.files_count}{prev_count} file{plural_files}"
        if not self.files_with_issues:
            if prev_files_with_issues == 1:
                return f"{processed_files_summary} but no issues were found. Previously there was 1 file with issues."
            return (
                f"{processed_files_summary} but no issues were found. "
                f"Previously there were {prev_files_with_issues} files with issues."
            )
        plural_files_with_issues = get_plural_form(len(self.files_with_issues))
        prev_count = f" ({get_string_diff(prev_files_with_issues, len(self.files_with_issues))})"
        return (
            f"{processed_files_summary} from which {len(self.files_with_issues)}{prev_count} "
            f"file{plural_files_with_issues} contained issues."
        )

    def get_report_without_compare(self) -> str:
        if not self.files_count:
            return "\nNo files were processed."
        plural_files = get_plural_form(self.files_count)
        processed_files_summary = f"\nProcessed {self.files_count} file{plural_files}"
        if not self.files_with_issues:
            return f"{processed_files_summary} but no issues were found."
        plural_files_with_issues = get_plural_form(len(self.files_with_issues))
        return (
            f"{processed_files_summary} from which {len(self.files_with_issues)} "
            f"file{plural_files_with_issues} contained issues."
        )
