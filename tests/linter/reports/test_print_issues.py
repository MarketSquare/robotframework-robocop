import os
import textwrap
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from robocop.linter.diagnostics import Diagnostic, Diagnostics, RunStatistic
from robocop.linter.fix import FixStats
from robocop.linter.reports.print_issues import PrintIssuesReport
from robocop.source_file import SourceFile


@pytest.fixture
def issues(empty_config, rule, rule2) -> Diagnostics:
    root = Path.cwd()
    source1_rel = "tests/atest/rules/comments/ignored-data/test.robot"
    source2_rel = "tests/atest/rules/misc/empty-return/test.robot"
    source1 = SourceFile(path=root / source1_rel, config=empty_config)
    source2 = SourceFile(path=root / source2_rel, config=empty_config)

    return Diagnostics(
        [
            Diagnostic(
                rule=r,
                source=source,
                node=None,
                model=None,
                lineno=line,
                col=col,
                end_lineno=end_line,
                end_col=end_col,
            )
            for r, source, line, end_line, col, end_col in [
                (rule, source1, 50, None, 10, None),
                (rule2, source1, 100, 51, 10, None),
                (rule, source2, 50, None, 10, 12),
                (rule2, source2, 11, 15, 10, 15),
            ]
        ]
    )


class TestPrintIssuesReport:
    def test_grouped_output_format(self, issues, empty_config, capsys):
        # arrange
        expected_output = (
            textwrap.dedent(r"""
        tests\atest\rules\comments\ignored-data\test.robot:
          50:10 0101 Some description (some-message)
          100:10 0902 Some description. Example (other-message)

        tests\atest\rules\misc\empty-return\test.robot:
          11:10 0902 Some description. Example (other-message)
          50:10 0101 Some description (some-message)

        Found 4 issues.
        """)
            .lstrip()
            .replace("\\", os.path.sep)
        )
        run_stats = RunStatistic(files_count=1, fix_stats=FixStats(), modified_files=[])
        report = PrintIssuesReport(empty_config)
        report.configure("output_format", "grouped")

        # act
        report.generate_report(issues, run_stats=run_stats)

        # assert
        out, _ = capsys.readouterr()
        assert out == expected_output

    def test_extended_with_encoding(self, issues, empty_config, capsys):
        """
        Check that an extended output format does not produce not supported characters.

        See bug https://github.com/MarketSquare/robotframework-robocop/issues/1539.
        """
        # arrange
        expected_output = r"tests\atest\rules\comments\ignored-data\test.robot:100:10".replace("\\", os.path.sep)
        source_lines = [""] * 200
        run_stats = RunStatistic(files_count=1, fix_stats=MagicMock(), modified_files=[])
        report = PrintIssuesReport(empty_config)
        report.configure("output_format", "extended")
        for diag in issues:
            diag.source._source_lines = source_lines  # noqa: SLF001

        # act
        report.generate_report(issues, run_stats=run_stats)

        # assert
        out, _ = capsys.readouterr()
        assert expected_output in out

    def test_extended_with_issue_format_configured(self, issues, empty_config, capsys):
        # Arrange - configure issue_format
        # - {source} - source file name | default
        # - {source_abs} - absolute path to a source file
        # - {line} - line number
        # - {end_line} - end line number
        # - {col} - column number
        # - {end_col} - end column number
        # - {severity} - severity level (info, warning, error)
        # - {rule_id} - rule id
        # - {desc} - rule description
        # - {name} - rule name
        issue_format = "{source} {source_abs} {line} {end_line} {col} {end_col} {severity} {rule_id} {desc} {name}"
        root = Path.cwd()
        source_path = "tests/atest/rules/comments/ignored-data/test.robot".replace("/", os.path.sep)
        expected_output = f"{source_path} {root / source_path} 50 50 10 10 W 0101 Some description some-message"
        source_lines = [""] * 200
        run_stats = RunStatistic(files_count=1, fix_stats=MagicMock(), modified_files=[])
        report = PrintIssuesReport(empty_config)
        report.configure("output_format", "extended")
        report.configure("issue_format", issue_format)
        for diag in issues:
            diag.source._source_lines = source_lines  # noqa: SLF001

        # act
        report.generate_report(issues, run_stats=run_stats)

        # assert
        out, _ = capsys.readouterr()
        assert expected_output in out
