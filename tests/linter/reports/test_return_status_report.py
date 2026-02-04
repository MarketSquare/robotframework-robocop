from pathlib import Path

import pytest

from robocop.linter.diagnostics import Diagnostic, Diagnostics
from robocop.linter.reports.return_status_report import ReturnStatusReport
from robocop.source_file import SourceFile


class TestReturnStatus:
    @pytest.mark.parametrize(
        ("param", "configuration", "quality_gates"),
        [
            ("quality_gate", "", {"E": 0, "W": 0, "I": -1}),
            ("quality_gates", "", {"E": 0, "W": 0, "I": -1}),
            ("quality_gates", "e=-1:w=-1:i=-1", {"E": -1, "W": -1, "I": -1}),
            ("quality_gates", "e=-1:w=-1:i=-1:r=0", {"E": -1, "W": -1, "I": -1}),
            ("quality_gates", "i=0", {"E": 0, "W": 0, "I": 0}),
            ("quality_gates", "E=100:W=100:I=100", {"E": 100, "W": 100, "I": 100}),
        ],
    )
    def test_quality_gates_configuration(self, param, configuration, quality_gates, empty_config):
        report = ReturnStatusReport(empty_config)
        report.configure(param, configuration)
        assert report.quality_gate == quality_gates

    @pytest.mark.parametrize(
        ("quality_gates", "return_status"),
        [
            ("", 20),
            ("e=-1", 10),
            ("i=0", 30),
            ("e=0:w=0:i=-1", 20),
            ("e=0:w=0:i=0", 30),
            ("e=0:w=-1:i=0", 20),
            ("e=-1:w=0:i=0", 20),
            ("e=-1:w=-1:i=-1", 0),
            ("e=-2:w=-2:i=-2", 0),
            ("e=10:w=10:i=10", 0),
            ("e=20:w=20:i=20", 0),
        ],
    )
    def test_return_status_with_quality_gates(
        self, empty_config, error_msg, warning_msg, info_msg, quality_gates, return_status
    ):
        report = ReturnStatusReport(empty_config)
        report.configure("quality_gates", quality_gates)
        issues = []
        source_file = SourceFile(path=Path(), config=empty_config)
        for _ in range(10):
            issues.append(
                Diagnostic(
                    rule=error_msg, source=source_file, model=None, lineno=1, col=1, end_lineno=None, end_col=None
                )
            )
            issues.append(
                Diagnostic(
                    rule=warning_msg, source=source_file, model=None, lineno=1, col=1, end_lineno=None, end_col=None
                )
            )
            issues.append(
                Diagnostic(
                    rule=info_msg, source=source_file, model=None, lineno=1, col=1, end_lineno=None, end_col=None
                )
            )
        report.generate_report(Diagnostics(issues))
        assert report.return_status == return_status

    def test_empty_results(self, empty_config):
        # Arrange
        report = ReturnStatusReport(empty_config)
        diagnostics = Diagnostics([])

        # Act
        report.generate_report(diagnostics)

        # Assert
        assert report.return_status == 0
