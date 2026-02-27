from __future__ import annotations

import sys
from difflib import unified_diff
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, NoReturn

from rich.console import Console
from rich.markup import escape
from rich.text import Text

import robocop.linter.reports
from robocop.files import get_relative_path
from robocop.formatter.utils.misc import decorate_diff_with_color

if TYPE_CHECKING:
    from robocop.config.schema import Config
    from robocop.linter.diagnostics import Diagnostic, Diagnostics, RunStatistic
    from robocop.source_file import SourceFile


class OutputFormat(Enum):
    SIMPLE = "simple"
    EXTENDED = "extended"
    GROUPED = "grouped"

    @classmethod
    def _missing_(cls, value: object) -> NoReturn:
        choices = [choice.value for choice in cls.__members__.values()]
        raise ValueError(f"{value} is not a valid {cls.__name__}, please choose from {choices}") from None


class PrintIssuesReport(robocop.linter.reports.Report):
    """
    **Report name**: ``print_issues``

    This report is always enabled.

    Report that prints diagnostic messages.

    There are available three different types of output:

    - extended (default), which print issue together with source code:

        test.robot:2:14 DEPR02 'Run Keyword If' is deprecated since Robot Framework version 5.*, use 'IF' instead
           |
         1 | *** Settings ***
         2 | Suite Setup  Run Keyword If
           |              ^^^^^^^^^^^^^^ DEPR02
         3 | Suite Teardown  Run Keyword If
         4 | Force Tags         tag
           |
    - grouped, which prints issues grouped by source files:

        templated_suite.robot:
          1:1 MISC06 No tests in 'templated_suite.robot' file, consider renaming to 'templated_suite.resource' (can-be-resource-file)
          2:18 DEPR02 'Run Keyword Unless' is deprecated since Robot Framework version 5.*, use 'IF' instead (deprecated-statement)

        test.robot:
          1:1 DOC03 Missing documentation in suite (missing-doc-suite)
          3:17 DEPR02 'Run Keyword If' is deprecated since Robot Framework version 5.*, use 'IF' instead (deprecated-statement)

    - simple, which print issue in one line. It also allows to configure format of message:

        variable_errors.robot:7:1 [E] ERR01 Robot Framework syntax error: Invalid dictionary variable item '1'. Items must use 'name=value' syntax or be dictionary variables themselves.
        positional_args.robot:3:32 [E] ERR01 Robot Framework syntax error: Positional argument '${arg2}' follows named argument

    You can configure output type with ``output_format``:

        robocop check --configure print_issues.output_format=grouped

    Format of simple output type can be configured with ``--issue-format`` option:

        robocop check --issue-format "{source}:{line}:{col} [{severity}] {rule_id} {desc} ({name})"

    Format of extended output type can be configured with ``issue_format`` parameter:

        robocop check --configure print_issues.issue_format="{source}"

    """  # noqa: E501

    NO_ALL = False
    ENABLED = True

    def __init__(self, config: Config) -> None:
        self.name = "print_issues"
        self.description = "Collect and print rules messages"
        self.output_format = OutputFormat.EXTENDED
        self.issue_format: str | None = None
        self.console = Console(highlight=False, soft_wrap=True, emoji=False)
        super().__init__(config)

    def configure(self, name: str, value: str) -> None:
        if name == "output_format":
            self.output_format = OutputFormat(value)
        elif name == "issue_format":
            self.issue_format = value
        else:
            super().configure(name, value)

    def print_diagnostics_simple(self, diagnostics: Diagnostics) -> None:
        for diag_by_source in diagnostics.diag_by_source.values():
            for diagnostic in diag_by_source:
                print(
                    self._get_formated_issue_message(
                        diagnostic.source.config.linter.issue_format, diagnostic, diagnostic.message
                    )
                )

    def print_diagnostics_grouped(self, diagnostics: Diagnostics) -> None:
        """
        Print diagnostics in grouped format.

        Example output:

            tests/suite.robot:
              63:10 E0101 Issue description

        """
        cwd = Path.cwd()
        grouped_format = "  {line}:{col} {rule_id} {desc} ({name})"
        for source, diag_by_source in diagnostics.diag_by_source.items():
            source_rel = get_relative_path(source, cwd)
            print(f"{source_rel}:")
            for diagnostic in diag_by_source:
                print(
                    grouped_format.format(
                        line=diagnostic.range.start.line,
                        col=diagnostic.range.start.character,
                        rule_id=diagnostic.rule.rule_id,
                        desc=diagnostic.message,
                        name=diagnostic.rule.name,
                    )
                )
            print()

    @staticmethod
    def _code_string(line: str, prefix: str) -> str:
        line = line.rstrip()
        if line:
            return prefix + line.expandtabs(4) + "\n"
        return "\n"

    @staticmethod
    def _get_formated_issue_message(issue_format: str, diagnostic: Diagnostic, message: str) -> str:
        return issue_format.format(
            source=diagnostic.source.relative_path,
            source_abs=diagnostic.source.path,
            line=diagnostic.range.start.line,
            col=diagnostic.range.start.character,
            end_line=diagnostic.range.end.line,
            end_col=diagnostic.range.end.character,
            severity=diagnostic.severity.value,
            rule_id=diagnostic.rule.rule_id,
            desc=message,
            name=diagnostic.rule.name,
        )

    def _print_issue_with_lines(self, lines: list[str], source_rel_path: Path, diagnostic: Diagnostic) -> Text:
        """
        Return a Rich Text object containing diagnostic information with source code lines.

        It highlights the problematic code section, displays the associated diagnostic message, and provides context
        by showing surrounding lines. The output is formatted with line numbers, gutter separators, and colored text
        for better readability.

        Args:
            lines: A list of strings representing the lines of the source file
            source_rel_path: The relative path to the source file where the diagnostic is located
            diagnostic: An object containing diagnostic information, including the range of the issue
            (start and end lines/columns), the rule ID, and the message

        """
        start_line, end_line = diagnostic.range.start.line, diagnostic.range.end.line
        start_col, end_col = diagnostic.range.start.character, diagnostic.range.end.character
        if self.issue_format is not None:
            text = Text.from_markup(
                self._get_formated_issue_message(self.issue_format, diagnostic, message=escape(diagnostic.message))
            )
            text.append("\n")
        else:
            text = Text(f"{source_rel_path}:{start_line}:{start_col} ")
            text.append(diagnostic.rule.rule_id, style="red")
            text.append(f" {diagnostic.message}\n")
        if diagnostic.rule.file_wide_rule or start_line > len(lines):
            return text
        start_line = max(start_line, 1)
        end_line = min(end_line, len(lines))
        gutter_width = len(str(end_line)) + 1
        gutter_space = " " * gutter_width
        text_lines: list[tuple[str, str] | str] = [(f"{gutter_space} |\n", "cyan")]
        # multi-line non-empty error lines will require indenting code before/after to match the error block
        if start_line == end_line or all(not lines[line_no].strip() for line_no in range(start_line, end_line + 1)):
            indent = ""
        else:
            indent = "  "
        # code before issue
        if start_line >= 2 and lines[start_line - 2].strip():  # no empty lines before
            start_line_cut = max(1, start_line - 2)  # take 2 lines before error if the lines exist
            for line_no in range(start_line_cut, start_line):
                text_lines.append((f"{line_no:>{gutter_width}} |", "cyan"))
                text_lines.append(self._code_string(lines[line_no - 1], prefix=f"{indent} "))
        # issue
        if start_line == end_line:  # error in one line (most cases)
            text_lines.append((f"{start_line:>{gutter_width}} |", "cyan"))
            text_lines.append(self._code_string(lines[start_line - 1], prefix=f"{indent} "))
            text_lines.append((f"{gutter_space} |{indent} ", "cyan"))
            text_lines.append(
                (
                    " " * (start_col - 1) + "^" * max(end_col - start_col, 1) + " " + diagnostic.rule.rule_id + "\n",
                    "red",
                )
            )
        else:  # multi-line errors, such as SPC05
            for line in range(start_line, end_line + 1):
                sep = "/" if line == start_line else "|"
                text_lines.append((f"{line:>{gutter_width}} | ", "cyan"))
                text_lines.append((f"{sep}", "red"))
                text_lines.append(self._code_string(lines[line - 1], prefix=" "))
            text_lines.append((f"{gutter_space} |", "cyan"))
            text_lines.append((f" |_^ {diagnostic.rule.rule_id}\n", "red"))
        # code after issue
        for line_no in range(end_line + 1, end_line + 3):
            if line_no > len(lines) or not lines[line_no - 1].strip():
                break
            text_lines.append((f"{line_no:>{gutter_width}} |{indent}", "cyan"))
            text_lines.append(self._code_string(lines[line_no - 1], prefix=" "))
        if diagnostic.rule.fix_suggestion:
            text_lines.append((f"{gutter_space} | ", "cyan"))
            text_lines.append(("Suggestion: ", "yellow"))
            text_lines.append(f"{diagnostic.rule.fix_suggestion}\n")
        text_lines.append((f"{gutter_space} |\n\n", "cyan"))
        text.append(Text.assemble(*text_lines))
        return text

    def print_diagnostics_extended(self, diagnostics: Diagnostics) -> None:
        """
        Print a diagnostics message with the surrounding source code.

        Messages are aggregated by source file and sent to printing to rich console.
        """
        for diag_by_source in diagnostics.diag_by_source.values():
            text: list[Text] = [
                self._print_issue_with_lines(
                    diagnostic.source.source_lines, diagnostic.source.relative_path, diagnostic
                )
                for diagnostic in diag_by_source
            ]
            self.console.print(*text, sep="", end="")

    def generate_report(self, diagnostics: Diagnostics, **kwargs: object) -> None:  # type: ignore[override]
        if self.config.silent:
            return
        run_stats: RunStatistic = kwargs["run_stats"]  # type: ignore[assignment]
        if run_stats and run_stats.files_count == 0:
            return
        if hasattr(sys.stdout, "reconfigure") and hasattr(sys.stderr, "reconfigure"):
            # Even if recent Python has it, it doesn't work for all the encoding without it
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        if not self.config.linter.diff:
            if self.output_format == OutputFormat.SIMPLE:
                self.print_diagnostics_simple(diagnostics)
                self.console.print()
            elif self.output_format == OutputFormat.GROUPED:
                self.print_diagnostics_grouped(diagnostics)
            elif self.output_format == OutputFormat.EXTENDED:
                self.print_diagnostics_extended(diagnostics)
            else:
                raise NotImplementedError(f"Output format {self.output_format} is not implemented")

        self.print_run_summary(diagnostics, run_stats)
        if self.config.linter.diff:
            self.console.print("Diff mode enabled. No files were modified. Run without --diff to apply fixes.")

    def print_run_summary(self, diagnostics: Diagnostics, run_stats: RunStatistic) -> None:
        """Print summary of applied fixes."""
        if run_stats and run_stats.fix_stats and run_stats.fix_stats.total_fixes != 0:
            self._print_diffs(run_stats.modified_files)
            summary = run_stats.fix_stats.format_summary()
            fixed = run_stats.fix_stats.total_fixes
            remaining = len(diagnostics.diagnostics)
            total = fixed + remaining
            suffix = "s" if total != 1 else ""
            summary += f"\nFound {total} issue{suffix} ({fixed} fixed, {remaining} remaining)."
        elif len(diagnostics.diagnostics) == 0:
            summary = "No issues found."
        else:
            suffix = "s" if len(diagnostics.diagnostics) != 1 else ""
            summary = f"Found {len(diagnostics.diagnostics)} issue{suffix}."
            could_fix = len(diagnostics.fixable_diagnostics())
            if could_fix > 0:
                summary += f"\n{could_fix} fixable with the ``--fix`` option."
        self.console.print(summary)

    def _print_diffs(self, modified_files: list[SourceFile]) -> None:
        """
        Print unified diffs for all modified files.

        Args:
            modified_files: List of source files that have been modified.

        """
        for source_file in modified_files:
            if not source_file.config.linter.diff:
                continue
            original = source_file.original_source_lines
            modified = source_file.source_lines

            diff = list(
                unified_diff(
                    original,
                    modified,
                    fromfile=f"before: {source_file.relative_path}",
                    tofile=f"after: {source_file.relative_path}",
                )
            )
            decorated_diff = decorate_diff_with_color(diff)
            for line in decorated_diff:
                self.console.print(line, end="")
            self.console.print()
