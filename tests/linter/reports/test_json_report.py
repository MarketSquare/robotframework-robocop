import json
from pathlib import Path

from robocop.linter.diagnostics import Diagnostics
from robocop.linter.reports.json_report import JsonReport
from tests.linter.reports import generate_issues


class TestJSONReport:
    def test_configure_output_dir(self, config):
        output_dir = "path/to/dir"
        report = JsonReport(config)
        report.configure("output_dir", output_dir)
        assert report.output_dir == Path(output_dir)

    def test_configure_filename(self, config):
        filename = ".robocop.json"
        report = JsonReport(config)
        report.configure("report_filename", filename)
        assert report.report_filename == filename

    def test_json_reports_saved_to_file(self, rule, rule2, tmp_path, config):
        issues = generate_issues(rule, rule2)
        report = JsonReport(config)
        report.configure("output_dir", tmp_path)

        expected_report = [
            {
                "column": 10,
                "description": "Some description",
                "end_column": 10,
                "end_line": 50,
                "line": 50,
                "rule_id": "0101",
                "rule_name": "some-message",
                "severity": "W",
                "source": "tests/atest/rules/comments/ignored-data/test.robot",
            },
            {
                "column": 10,
                "description": "Some description. Example",
                "end_column": 10,
                "end_line": 51,
                "line": 50,
                "rule_id": "0902",
                "rule_name": "other-message",
                "severity": "E",
                "source": "tests/atest/rules/comments/ignored-data/test.robot",
            },
            {
                "column": 10,
                "description": "Some description",
                "end_column": 12,
                "end_line": 50,
                "line": 50,
                "rule_id": "0101",
                "rule_name": "some-message",
                "severity": "W",
                "source": "tests/atest/rules/misc/empty-return/test.robot",
            },
            {
                "column": 10,
                "description": "Some description. Example",
                "end_column": 15,
                "end_line": 15,
                "line": 11,
                "rule_id": "0902",
                "rule_name": "other-message",
                "severity": "E",
                "source": "tests/atest/rules/misc/empty-return/test.robot",
            },
        ]
        report.generate_report(Diagnostics(issues))
        json_path = report.output_dir / "robocop.json"
        with open(json_path) as fp:
            json_report = json.load(fp)
        assert json_report == expected_report
