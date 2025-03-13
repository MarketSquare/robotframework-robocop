import json
from unittest import mock

from robocop.linter.reports.gitlab import GitlabReport
from tests.linter.reports import generate_issues


class TestGitlabReport:
    def test_gitlab_report(self, rule, rule2, config, tmp_path):
        output_file = tmp_path / "reports" / "report.json"
        issues = generate_issues(rule, rule2)
        issues[0].range.start.line = 1
        issues[0].range.end.line = 1
        issues[1].range.start.line = 2
        issues[1].range.end.line = 2
        issues[2].range.start.line = 1
        issues[2].range.end.line = 1
        issues[3].range.start.line = 2
        issues[3].range.end.line = 2
        issues.append(issues[2])
        issues[4].range.start.line = 2
        issues[4].range.end.line = 2
        expected_report = [
            {
                "check_name": "some-message",
                "description": "Some description",
                "fingerprint": "1be5653ab24aa7ff31a65acff80621fe09e5b31f",
                "location": {"lines": {"begin": 1}, "path": "tests/atest/rules/comments/ignored-data/test.robot"},
                "severity": "minor",
            },
            {
                "check_name": "other-message",
                "description": "Some description. Example",
                "fingerprint": "9841ed60f7af5c1fff6727dae96af16ccf8bb152",
                "location": {"lines": {"begin": 2}, "path": "tests/atest/rules/comments/ignored-data/test.robot"},
                "severity": "major",
            },
            {
                "check_name": "some-message",
                "description": "Some description",
                "fingerprint": "fdf047043356a7d73bc1f4a335c682930aca0e18",
                "location": {"lines": {"begin": 2}, "path": "tests/atest/rules/misc/empty-return/test.robot"},
                "severity": "minor",
            },
            {
                "check_name": "some-message",
                "description": "Some description",
                "fingerprint": "3a2a89f126310a3559629c7056ced04141e6597c",
                "location": {"lines": {"begin": 2}, "path": "tests/atest/rules/misc/empty-return/test.robot"},
                "severity": "minor",
            },
            {
                "check_name": "other-message",
                "description": "Some description. Example",
                "fingerprint": "01db54652f4a2f86dc6248dff586d62f66313b59",
                "location": {"lines": {"begin": 2}, "path": "tests/atest/rules/misc/empty-return/test.robot"},
                "severity": "major",
            },
        ]
        report = GitlabReport(config)
        report.configure("output_path", output_file)
        for issue in issues:
            report.add_message(issue)
        # content of 1 and 2 file. 2 file use the same lines to check if fingerprint will be different
        content = [["line1", "line2"], ["line1", "line1"]]
        with mock.patch.object(report, "_get_source_lines", side_effect=content):
            report.get_report()
        with open(output_file) as fp:
            json_report = json.load(fp)
        assert json_report == expected_report

    def test_configure_output_path(self, config):
        output_path = "path/to/dir/file.json"
        report = GitlabReport(config)
        report.configure("output_path", output_path)
        assert report.output_path == output_path
