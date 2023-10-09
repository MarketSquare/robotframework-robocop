from typing import Dict

import robocop.reports
from robocop.rules import Message
from robocop.utils.misc import get_string_diff


class FileStatsReport(robocop.reports.ComparableReport):
    """
    **Report name**: ``file_stats``

    Report that displays overall statistics about number of processed files.

    Example::

        Processed 7 files from which 5 files contained issues.
    """

    def __init__(self, compare_runs):
        self.name = "file_stats"
        self.description = "Prints overall statistics about number of processed files"
        self.files_count = 0
        self.files_with_issues = set()
        super().__init__(compare_runs)

    def add_message(self, message: Message):
        self.files_with_issues.add(message.source)

    def persist_result(self):
        return {"files_count": self.files_count, "files_with_issues": len(self.files_with_issues)}

    @staticmethod
    def get_plural(count):
        return "s" if count != 1 else ""

    def get_report(self, prev_results: Dict) -> str:
        if self.compare_runs and prev_results:
            return self.get_report_with_compare(prev_results)
        return self.get_report_without_compare()

    def get_report_with_compare(self, prev_results: Dict) -> str:
        plural_files = self.get_plural(self.files_count)
        prev_files_count = prev_results["files_count"]
        prev_files_with_issues = prev_results["files_with_issues"]
        if not self.files_count:
            if prev_files_count == 1:
                return "\nNo files were processed. Previously 1 file was processed."
            else:
                return f"\nNo files were processed. Previously {prev_files_count} files were processed."
        prev_count = f" ({get_string_diff(prev_files_count, self.files_count)})"
        processed_files_summary = f"\nProcessed {self.files_count}{prev_count} file{plural_files}"
        if not self.files_with_issues:
            if prev_files_with_issues == 1:
                return f"{processed_files_summary} but no issues were found. Previously there was 1 file with issues."
            else:
                return (
                    f"{processed_files_summary} but no issues were found. "
                    f"Previously there were {prev_files_with_issues} files with issues."
                )
        plural_files_with_issues = self.get_plural(len(self.files_with_issues))
        prev_count = f" ({get_string_diff(prev_files_with_issues, len(self.files_with_issues))})"
        return (
            f"{processed_files_summary} from which {len(self.files_with_issues)}{prev_count} "
            f"file{plural_files_with_issues} contained issues."
        )

    def get_report_without_compare(self) -> str:
        if not self.files_count:
            return "\nNo files were processed."
        plural_files = self.get_plural(self.files_count)
        processed_files_summary = f"\nProcessed {self.files_count} file{plural_files}"
        if not self.files_with_issues:
            return f"{processed_files_summary} but no issues were found."
        plural_files_with_issues = self.get_plural(len(self.files_with_issues))
        return (
            f"{processed_files_summary} from which {len(self.files_with_issues)} "
            f"file{plural_files_with_issues} contained issues."
        )
