import json
from pathlib import Path

import robocop.linter.reports
from robocop.config import Config
from robocop.linter.diagnostics import Diagnostic


class JsonReport(robocop.linter.reports.Report):
    r"""
    **Report name**: ``json_report``

    Report that returns a list of found issues in a JSON format. The output file will be generated
    in the current working directory with the ``robocop.json`` name.

    This report is not included in the default reports. The ``--reports all`` option will not enable this report.
    You can still enable it using report name directly: ``--reports json_report`` or ``--reports all,json_report``.

    You can configure output directory and report filename::

        robocop check --configure json_report.output_dir=C:/json_reports
        robocop check --configure json_report.report_filename=robocop_output.json

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
        self.output_dir = None
        self.report_filename = "robocop.json"
        self.issues = []
        super().__init__(config)

    def add_message(self, message: Diagnostic) -> None:
        self.issues.append(self.message_to_json(message))

    def get_report(self) -> str:
        if self.output_dir is not None:
            output_path = self.output_dir / self.report_filename
        else:
            output_path = Path(self.report_filename)
        with open(output_path, "w") as fp:
            json_string = json.dumps(self.issues, indent=4)
            fp.write(json_string)
        return f"\nGenerated JSON report at {output_path}"

    def configure(self, name: str, value: str) -> None:
        if name == "output_dir":
            self.output_dir = Path(value)
            self.output_dir.mkdir(parents=True, exist_ok=True)
        elif name == "report_filename":
            self.report_filename = value
        else:
            super().configure(name, value)

    @staticmethod
    def message_to_json(message: Diagnostic) -> dict:
        return {
            "source": message.source,
            "line": message.range.start.line,
            "end_line": message.range.end.line,
            "column": message.range.start.character,
            "end_column": message.range.end.character,
            "severity": message.severity.value,
            "rule_id": message.rule.rule_id,
            "description": message.message,
            "rule_name": message.rule.name,
        }
