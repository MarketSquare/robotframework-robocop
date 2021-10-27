import pytest

from robocop.reports import FileStatsReport, JsonReport
from robocop.rules import Message, Rule, RuleParam, RuleSeverity


@pytest.fixture
def message():
    return Rule(
        RuleParam(name="param_name", converter=int, default=1, desc=""),
        rule_id="0101",
        name="some-message",
        msg="Some description",
        severity=RuleSeverity.WARNING,
    )


class TestReports:
    def test_json_report(self, message):
        report = JsonReport()
        issue = Message(
            rule=message,
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
            "column": 10,
            "line": 50,
            "rule_id": "0101",
            "rule_name": "some-message",
            "severity": "W",
            "description": "Some description",
        }

    @pytest.mark.parametrize(
        "files, files_with_issues, output",
        [
            (0, set(), "\nNo files were processed"),
            (10, set(), "\nProcessed 10 file(s) but no issues were found"),
            (
                10,
                {"a.robot", "b.robot"},
                "\nProcessed 10 file(s) from which 3 file(s) contained issues",
            ),
        ],
    )
    def test_file_stats_report(self, files, files_with_issues, output, message):
        report = FileStatsReport()
        report.files_count = files
        report.files_with_issues = files_with_issues
        if files_with_issues:
            issue = Message(
                rule=message,
                source="some/path/file.robot",
                node=None,
                lineno=50,
                col=10,
                end_lineno=None,
                end_col=None,
            )
            report.add_message(issue)
        assert report.get_report() == output
