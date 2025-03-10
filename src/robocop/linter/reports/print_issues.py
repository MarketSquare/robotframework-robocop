from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, NoReturn

from rich.console import Console
from rich.markup import escape

import robocop.linter.reports
from robocop.formatter.utils.misc import StatementLinesCollector

if TYPE_CHECKING:
    from robot.parsing import File

    from robocop.config import Config
    from robocop.linter.diagnostics import Diagnostic


class OutputFormat(Enum):
    SIMPLE = "simple"
    EXTENDED = "extended"
    GROUPED = "grouped"

    @classmethod
    def _missing_(cls, value) -> NoReturn:
        choices = [choice.value for choice in cls.__members__.values()]
        raise ValueError(f"{value} is not a valid {cls.__name__}, please choose from {choices}") from None


class PrintIssuesReport(robocop.linter.reports.Report):
    """
    **Report name**: ``print_issues``

    This report is always enabled.
    Report that collect diagnostic messages and print them at the end of the execution.
    """

    NO_ALL = False
    ENABLED = True

    def __init__(self, config: Config):
        self.name = "print_issues"
        self.description = "Collect and print rules messages"
        self.diagn_by_source: dict[str, list[Diagnostic]] = {}
        self.output_format = OutputFormat.EXTENDED
        self.console = Console(highlight=False, soft_wrap=True)
        super().__init__(config)

    def configure(self, name: str, value: str) -> None:
        if name == "output_format":
            self.output_format = OutputFormat(value)
        else:
            super().configure(name, value)

    def add_message(self, message: Diagnostic) -> None:
        if message.source not in self.diagn_by_source:
            self.diagn_by_source[message.source] = []
        self.diagn_by_source[message.source].append(message)

    def print_diagnostics_simple(self) -> None:
        cwd = Path.cwd()
        for source, diagnostics in self.diagn_by_source.items():
            diagnostics.sort()
            source_rel = Path(source).relative_to(cwd)
            for diagnostic in diagnostics:
                print(
                    self.config.linter.issue_format.format(
                        source=source_rel,
                        source_abs=diagnostic.source,
                        line=diagnostic.range.start.line,
                        col=diagnostic.range.start.character,
                        end_line=diagnostic.range.end.line,
                        end_col=diagnostic.range.end.character,
                        severity=diagnostic.severity.value,
                        rule_id=diagnostic.rule.rule_id,
                        desc=diagnostic.message,
                        name=diagnostic.rule.name,
                    )
                )

    def print_diagnostics_grouped(self) -> None:
        """
        Print diagnostics in grouped format.

        Example output:

            tests/suite.robot:
              63:10 E0101 Issue description

        """
        cwd = Path.cwd()
        grouped_format = "  {line}:{col} {rule_id} {desc} ({name})"
        for source, diagnostics in self.diagn_by_source.items():
            diagnostics.sort()
            source_rel = Path(source).relative_to(cwd)
            print(f"{source_rel}:")
            for diagnostic in diagnostics:
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
    def _get_source_lines(model: File) -> list[str]:
        return StatementLinesCollector(model).text.splitlines()

    @staticmethod
    def _gutter(line_no: int | str, gutter_width: int, indent: str):
        return f"[cyan]{line_no:>{gutter_width}} |[/cyan]{indent}"

    def _print_lines(self, lines: list[str]) -> None:
        self.console.print("\n".join(line.rstrip() for line in lines))

    def _print_issue_with_lines(self, lines: list[str], source_rel_path: Path, diagnostic: Diagnostic) -> None:
        """
        Print diagnostic information for a specific range of lines in a source file.

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
        self.console.print(
            f"{source_rel_path}:{start_line}:{start_col} "
            f"[red]{diagnostic.rule.rule_id}[/red] {escape(diagnostic.message)}"
        )
        if diagnostic.rule.file_wide_rule or start_line > len(lines):
            return
        start_line = max(start_line, 1)
        end_line = min(end_line, len(lines))
        gutter_width = len(str(end_line)) + 1
        # multi-line non-empty error lines will require indenting code before/after to match error block
        if start_line == end_line or all(not lines[line_no].strip() for line_no in range(start_line, end_line + 1)):
            indent = ""
        else:
            indent = "  "
        print_lines = [self._gutter(" ", gutter_width, "")]
        # code before issue
        if start_line >= 2 and lines[start_line - 2].strip():  # no empty lines before
            for line_no in range(start_line - 2, start_line):
                if line_no < 1:
                    continue
                print_lines.append(f"{self._gutter(line_no, gutter_width, indent)} {escape(lines[line_no - 1])}")
        # issue
        if start_line == end_line:  # error in one line (most cases)
            print_lines.append(f"{self._gutter(start_line, gutter_width, indent)} {escape(lines[start_line - 1])}")
            print_lines.append(
                f"{self._gutter(' ', gutter_width, indent)} "
                f"[red]{' ' * (start_col - 1)}{'^' * max(end_col - start_col, 1)} {diagnostic.rule.rule_id}[/red]"
            )
        else:  # multi line errors, such as SPC05
            for line in range(start_line, end_line + 1):
                sep = "/" if line == start_line else "|"
                print_lines.append(
                    f"{self._gutter(line, gutter_width, indent='')} [red]{sep}[/red] {escape(lines[line - 1])}"
                )
            print_lines.append(f"{self._gutter(' ', gutter_width, indent='')} [red]|_^ {diagnostic.rule.rule_id}[/red]")
        # code after issue
        for line_no in range(end_line + 1, end_line + 3):
            if line_no > len(lines) or not lines[line_no - 1].strip():
                break
            print_lines.append(f"{self._gutter(line_no, gutter_width, indent)} {escape(lines[line_no - 1])}")
        print_lines.append(self._gutter(" ", gutter_width, ""))
        self._print_lines(print_lines)
        print()

    def print_diagnostics_extended(self) -> None:
        cwd = Path.cwd()
        for source, diagnostics in self.diagn_by_source.items():
            diagnostics.sort()
            source_rel = Path(source).relative_to(cwd)
            source_lines = None
            for diagnostic in diagnostics:
                if not source_lines:  # TODO: model should be coming from source, not diagnostics
                    source_lines = self._get_source_lines(diagnostic.model)
                self._print_issue_with_lines(source_lines, source_rel, diagnostic)

    def get_report(self) -> None:
        if self.output_format == OutputFormat.SIMPLE:
            self.print_diagnostics_simple()
        elif self.output_format == OutputFormat.GROUPED:
            self.print_diagnostics_grouped()
        elif self.output_format == OutputFormat.EXTENDED:
            self.print_diagnostics_extended()
        else:
            raise NotImplementedError(f"Output format {self.output_format} is not implemented")
