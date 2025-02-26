import json
from pathlib import Path

import pytest

from robocop.config import Config
from robocop.linter.reports.json_report import InternalJsonReport, JsonReport
from robocop.linter.rules import Message


class TestJSONReport:
    @pytest.mark.parametrize("json_class", [JsonReport, InternalJsonReport])
    def test_json_report(self, rule, json_class):
        report = json_class()
        issue = Message(
            rule=rule,
            msg=rule.get_message(),
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

    def test_configure_output_dir(self):
        output_dir = "path/to/dir"
        report = JsonReport()
        report.configure("output_dir", output_dir)
        assert report.output_dir == Path(output_dir)

    def test_configure_filename(self):
        filename = ".robocop.json"
        report = JsonReport()
        report.configure("report_filename", filename)
        assert report.report_filename == filename

    @pytest.mark.parametrize("previous_results", [None, {}, {"issue": 10}])
    @pytest.mark.parametrize("compare_runs", [True, False])
    def test_json_reports_saved_to_file(self, rule, rule2, compare_runs, previous_results, tmp_path):
        root = Path(".").resolve()
        source1_rel = "tests/atest/rules/comments/ignored-data/test.robot"
        source2_rel = "tests/atest/rules/misc/empty-return/test.robot"
        source1 = str(root / source1_rel)
        source2 = str(root / source2_rel)

        report = JsonReport()
        report.configure("output_dir", tmp_path)

        issues = [
            Message(
                rule=r,
                msg=r.get_message(),
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

        expected_report = [issue.to_json() for issue in issues]
        for issue in issues:
            report.add_message(issue)
        report.get_report()
        json_path = report.output_dir / "robocop.json"
        with open(json_path) as fp:
            json_report = json.load(fp)
        assert expected_report == json_report
