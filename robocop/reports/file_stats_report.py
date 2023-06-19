from robocop.reports import Report
from robocop.rules import Message


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
