import json
from pathlib import Path

from robocop.linter.diagnostics import Diagnostic
from robocop.linter.reports.json_report import JsonReport
from tests.linter.reports import generate_issues


class TestJSONReport:
    def test_json_report(self, rule, config):
        report = JsonReport(config)
        issue = Diagnostic(
            rule=rule,
            source="some/path/file.robot",
            node=None,
            lineno=50,
            col=10,
            end_lineno=None,
            end_col=None,
        )
        report.add_message(issue)
        assert report.issues[0] == {
            "source": "some/path/file.robot",
            "line": 50,
            "end_line": 50,
            "column": 10,
            "end_column": 10,
            "rule_id": "0101",
            "rule_name": "some-message",
            "severity": "W",
            "description": "Some description",
        }

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

        expected_report = [JsonReport.message_to_json(issue) for issue in issues]
        for issue in issues:
            report.add_message(issue)
        report.get_report()
        json_path = report.output_dir / "robocop.json"
        with open(json_path) as fp:
            json_report = json.load(fp)
        assert expected_report == json_report
