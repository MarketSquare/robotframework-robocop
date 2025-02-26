import os
import textwrap
from pathlib import Path

import pytest

from robocop.linter.diagnostics import Diagnostic
from robocop.linter.reports.print_issues import PrintIssuesReport


@pytest.fixture
def issues(rule, rule2) -> list[Diagnostic]:
    root = Path.cwd()
    source1_rel = "tests/atest/rules/comments/ignored-data/test.robot"
    source2_rel = "tests/atest/rules/misc/empty-return/test.robot"
    source1 = str(root / source1_rel)
    source2 = str(root / source2_rel)

    return [
        Diagnostic(
            rule=r,
            source=source,
            node=None,
            lineno=line,
            col=col,
            end_lineno=end_line,
            end_col=end_col,
        )
        for r, source, line, end_line, col, end_col in [
            (rule, source1, 50, None, 10, None),
            (rule2, source1, 50, 51, 10, None),
            (rule, source2, 50, None, 10, 12),
            (rule2, source2, 11, 15, 10, 15),
        ]
    ]


class TestPrintIssuesReport:
    def test_grouped_output_format(self, issues, config, capsys):
        # arrange
        expected_output = (
            textwrap.dedent(r"""
        tests\atest\rules\comments\ignored-data\test.robot:
          50:10 0101 Some description (some-message)
          50:10 0902 Some description. Example (other-message)

        tests\atest\rules\misc\empty-return\test.robot:
          11:10 0902 Some description. Example (other-message)
          50:10 0101 Some description (some-message)

        """)
            .lstrip()
            .replace("\\", os.path.sep)
        )
        report = PrintIssuesReport(config)
        report.configure("output_format", "grouped")
        for issue in issues:
            report.add_message(issue)

        # act
        report.get_report()

        # assert
        out, _ = capsys.readouterr()
        assert out == expected_output
