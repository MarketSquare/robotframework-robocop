from pathlib import Path

import robocop.linter.reports
from robocop.config import Config
from robocop.files import get_relative_path
from robocop.linter.diagnostics import Diagnostic, Diagnostics


class JsonReport(robocop.linter.reports.JsonFileReport):
    r"""
    **Report name**: ``json_report``

    Report that returns a list of found issues in a JSON format. The output file will be generated
    in the current working directory with the ``robocop.json`` name.

    This report is not included in the default reports. The ``--reports all`` option will not enable this report.
    You can still enable it using report name directly: ``--reports json_report`` or ``--reports all,json_report``.

    You can configure output path. It's relative path to file that will be produced by the report::

        robocop check --configure json_report.output_path=C:/json_reports/report.json

    Default path is ``robocop.json`` .

    Example content of the file::

        [
            {
                "source": "C:\robot_tests\keywords.robot",
                "line": 1,
                "end_line": 1,
                "column": 1,
                "end_column": 1,
                "severity": "I",
                "rule_id": "0913",
                "description": "No tests in 'keywords.robot' file, consider renaming to 'keywords.resource'",
                "rule_name": "can-be-resource-file"
            },
            {
                "source": "C:\\robot_tests\\keywords.robot",
                "line": 51,
                "end_line": 51,
                "column": 1,
                "end_column": 13,
                "severity": "W",
                "rule_id": "0324",
                "description": "Variable '${TEST_NAME}' overwrites reserved variable '${TEST_NAME}'",
                "rule_name": "overwriting-reserved-variable"
            }
        ]

    """

    NO_ALL = False

    def __init__(self, config: Config):
        self.name = "json_report"
        self.description = "Produces JSON file with found issues"
        super().__init__(output_path="robocop.json", config=config)

    def generate_report(self, diagnostics: Diagnostics, **kwargs) -> None:  # noqa: ARG002
        issues = [self.message_to_json(diagnostic) for diagnostic in diagnostics]
        super().generate_report(issues, "JSON")

    @staticmethod
    def message_to_json(message: Diagnostic) -> dict:
        source_rel = get_relative_path(message.source, Path.cwd()).as_posix()
        return {
            "source": str(source_rel),
            "line": message.range.start.line,
            "end_line": message.range.end.line,
            "column": message.range.start.character,
            "end_column": message.range.end.character,
            "severity": message.severity.value,
            "rule_id": message.rule.rule_id,
            "description": message.message,
            "rule_name": message.rule.name,
        }
