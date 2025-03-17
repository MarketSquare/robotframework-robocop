import json

from robocop.linter.diagnostics import Diagnostics
from robocop.linter.reports.json_report import JsonReport
from tests.linter.reports import generate_issues


class TestJSONReport:
    def test_configure_output_path(self, config):
        output_path = "path/to/dir/file.json"
        report = JsonReport(config)
        report.configure("output_path", output_path)
        assert report.output_path == output_path

    def test_json_reports_saved_to_file(self, rule, rule2, tmp_path, config):
        issues = generate_issues(rule, rule2)
        output_file = tmp_path / "robocop.json"
        report = JsonReport(config)
        report.configure("output_path", str(output_file))

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
        with open(output_file) as fp:
            json_report = json.load(fp)
        assert json_report == expected_report
