from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, NoReturn

from rich.console import Console
from rich.markup import escape

import robocop.linter.reports
from robocop.files import get_relative_path
from robocop.formatter.utils.misc import StatementLinesCollector

if TYPE_CHECKING:
    from robot.parsing import File

    from robocop.config import Config
    from robocop.linter.diagnostics import Diagnostic, Diagnostics


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

    There are available three different types of output:

    - extended (default), which print issue together with source code::

        test.robot:2:14 DEPR02 'Run Keyword If' is deprecated since Robot Framework version 5.*, use 'IF' instead
           |
         1 | *** Settings ***
         2 | Suite Setup  Run Keyword If
           |              ^^^^^^^^^^^^^^ DEPR02
         3 | Suite Teardown  Run Keyword If
         4 | Force Tags         tag
           |
    - grouped, which prints issues grouped by source files::

        templated_suite.robot:
          1:1 MISC06 No tests in 'templated_suite.robot' file, consider renaming to 'templated_suite.resource' (can-be-resource-file)
          2:18 DEPR02 'Run Keyword Unless' is deprecated since Robot Framework version 5.*, use 'IF' instead (deprecated-statement)

        test.robot:
          1:1 DOC03 Missing documentation in suite (missing-doc-suite)
          3:17 DEPR02 'Run Keyword If' is deprecated since Robot Framework version 5.*, use 'IF' instead (deprecated-statement)

    - simple, which print issue in one line. It also allows to configure format of message::

        variable_errors.robot:7:1 [E] ERR01 Robot Framework syntax error: Invalid dictionary variable item '1'. Items must use 'name=value' syntax or be dictionary variables themselves.
        positional_args.robot:3:32 [E] ERR01 Robot Framework syntax error: Positional argument '${arg2}' follows named argument

    You can configure output type with ``output_format``::

        robocop check --configure print_issues.output_format=grouped

    Format of simple output type can be configured with ``--issue-format`` option::

        robocop check --issue-format "{source}:{line}:{col} [{severity}] {rule_id} {desc} ({name})"

    Format of extended output type can be configured with ``issue_format`` parameter::

        robocop check --configure print_issues.issue_format="{source}"

    """  # noqa: E501

    NO_ALL = False
    ENABLED = True

    def __init__(self, config: Config):
        self.name = "print_issues"
        self.description = "Collect and print rules messages"
        self.diagn_by_source: dict[str, list[Diagnostic]] = {}
        self.output_format = OutputFormat.EXTENDED
        self.issue_format = None
        self.console = Console(highlight=False, soft_wrap=True)
        super().__init__(config)

    def configure(self, name: str, value: str) -> None:
        if name == "output_format":
            self.output_format = OutputFormat(value)
        elif name == "issue_format":
            self.issue_format = value
        else:
            super().configure(name, value)

    def print_diagnostics_simple(self, diagnostics: Diagnostics) -> None:
        cwd = Path.cwd()
        for source, diag_by_source in diagnostics.diag_by_source.items():
            source_rel = get_relative_path(source, cwd)
            for diagnostic in diag_by_source:
                print(
                    self.config.linter.issue_format.format(
                        source=source_rel,
                        source_abs=str(Path(source).resolve()),
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
    def _get_source_lines(model: File) -> list[str]:
        return StatementLinesCollector(model).text.splitlines()

    @staticmethod
    def _gutter(line_no: int | str, gutter_width: int, indent: str):
        return f"[cyan]{line_no:>{gutter_width}} |[/cyan]{indent}"

    def _print_lines(self, lines: list[str]) -> None:
        self.console.print("\n".join(line.expandtabs(4).rstrip() for line in lines))

    def _code_string(self, line: str) -> str:
        return escape(line.expandtabs(4))

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
        issue_format = (
            self.issue_format if self.issue_format is not None else "{source}:{line}:{col} [red]{rule_id}[/red] {desc}"
        )
        issue_msg = issue_format.format(
            source=source_rel_path,
            line=start_line,
            col=start_col,
            rule_id=diagnostic.rule.rule_id,
            desc=escape(diagnostic.message),
        )
        self.console.print(issue_msg)
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
                print_lines.append(
                    f"{self._gutter(line_no, gutter_width, indent)} {self._code_string(lines[line_no - 1])}"
                )
        # issue
        if start_line == end_line:  # error in one line (most cases)
            print_lines.append(
                f"{self._gutter(start_line, gutter_width, indent)} {self._code_string(lines[start_line - 1])}"
            )
            print_lines.append(
                f"{self._gutter(' ', gutter_width, indent)} "
                f"[red]{' ' * (start_col - 1)}{'^' * max(end_col - start_col, 1)} {diagnostic.rule.rule_id}[/red]"
            )
        else:  # multi line errors, such as SPC05
            for line in range(start_line, end_line + 1):
                sep = "/" if line == start_line else "|"
                print_lines.append(
                    f"{self._gutter(line, gutter_width, indent='')} [red]{sep}[/red] "
                    f"{self._code_string(lines[line - 1])}"
                )
            print_lines.append(f"{self._gutter(' ', gutter_width, indent='')} [red]|_^ {diagnostic.rule.rule_id}[/red]")
        # code after issue
        for line_no in range(end_line + 1, end_line + 3):
            if line_no > len(lines) or not lines[line_no - 1].strip():
                break
            print_lines.append(f"{self._gutter(line_no, gutter_width, indent)} {self._code_string(lines[line_no - 1])}")
        print_lines.append(self._gutter(" ", gutter_width, ""))
        self._print_lines(print_lines)
        print()

    def print_diagnostics_extended(self, diagnostics: Diagnostics) -> None:
        cwd = Path.cwd()
        for source, diag_by_source in diagnostics.diag_by_source.items():
            source_rel = get_relative_path(source, cwd)
            source_lines = None
            for diagnostic in diag_by_source:
                if not source_lines:  # TODO: model should be coming from source, not diagnostics
                    source_lines = self._get_source_lines(diagnostic.model)
                self._print_issue_with_lines(source_lines, source_rel, diagnostic)

    def generate_report(self, diagnostics: Diagnostics, **kwargs) -> None:  # noqa: ARG002
        if self.output_format == OutputFormat.SIMPLE:
            self.print_diagnostics_simple(diagnostics)
        elif self.output_format == OutputFormat.GROUPED:
            self.print_diagnostics_grouped(diagnostics)
        elif self.output_format == OutputFormat.EXTENDED:
            self.print_diagnostics_extended(diagnostics)
        else:
            raise NotImplementedError(f"Output format {self.output_format} is not implemented")
