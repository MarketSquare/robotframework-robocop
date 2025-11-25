import os
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from robocop.linter.diagnostics import Diagnostic, Diagnostics
from robocop.linter.reports.print_issues import PrintIssuesReport


@pytest.fixture
def issues(rule, rule2) -> Diagnostics:
    root = Path.cwd()
    source1_rel = "tests/atest/rules/comments/ignored-data/test.robot"
    source2_rel = "tests/atest/rules/misc/empty-return/test.robot"
    source1 = str(root / source1_rel)
    source2 = str(root / source2_rel)

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
    def test_grouped_output_format(self, issues, config, capsys):
        # arrange
        expected_output = (
            textwrap.dedent(r"""
        tests\atest\rules\comments\ignored-data\test.robot:
          50:10 0101 Some description (some-message)
          100:10 0902 Some description. Example (other-message)

        tests\atest\rules\misc\empty-return\test.robot:
          11:10 0902 Some description. Example (other-message)
          50:10 0101 Some description (some-message)

        """)
            .lstrip()
            .replace("\\", os.path.sep)
        )
        report = PrintIssuesReport(config)
        report.configure("output_format", "grouped")

        # act
        report.generate_report(issues)

        # assert
        out, _ = capsys.readouterr()
        assert out == expected_output

    def test_extended_with_encoding(self, issues, config, capsys):
        """
        Check that an extended output format does not produce not supported characters.

        See bug https://github.com/MarketSquare/robotframework-robocop/issues/1539.
        """
        # arrange
        expected_output = r"tests\atest\rules\comments\ignored-data\test.robot:100:10".replace("\\", os.path.sep)
        source_lines = [""] * 200
        report = PrintIssuesReport(config)
        report.configure("output_format", "extended")

        # act
        with patch.object(report, "_get_source_lines", return_value=source_lines):
            report.generate_report(issues)

        # assert
        out, _ = capsys.readouterr()
        assert expected_output in out
