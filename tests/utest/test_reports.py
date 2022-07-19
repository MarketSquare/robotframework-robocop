import pytest
import re

from robocop.reports import FileStatsReport, JsonReport, RobocopVersionReport, TimestampReport
from robocop.rules import Message, Rule, RuleParam, RuleSeverity
from robocop.version import __version__
from robocop.exceptions import ConfigGeneralError

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
            msg=message.get_message(),
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
            (0, set(), "\nNo files were processed."),
            (10, set(), "\nProcessed 10 files but no issues were found."),
            (
                10,
                {"a.robot", "b.robot"},
                "\nProcessed 10 files from which 3 files contained issues.",
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
                msg=message.get_message(),
                source="some/path/file.robot",
                node=None,
                lineno=50,
                col=10,
                end_lineno=None,
                end_col=None,
            )
            report.add_message(issue)
        assert report.get_report() == output

    def test_version_report(self, message):
        report = RobocopVersionReport()
        issue = Message(
            rule=message,
            msg=message.get_message(),
            source="some/path/file.robot",
            node=None,
            lineno=50,
            col=10,
            end_lineno=None,
            end_col=None,
        )
        report.add_message(issue)
        assert __version__ in report.get_report()

    def test_timestamp_report(self, message):
        report = TimestampReport()
        issue = Message(
            rule=message,
            msg=message.get_message(),
            source="some/path/file.robot",
            node=None,
            lineno=50,
            col=10,
            end_lineno=None,
            end_col=None,
        )
        report.add_message(issue)
        assert "Reported: " in report.get_report()

    @pytest.mark.parametrize(
        "name, value, expected",
        [
            ("timezone", "UTC", r"\+0000"),
            ("format", "hello", r"Reported: hello"),
            ("format", "%Y-%m-%dT%H:%M:%S", r".*([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2})"),
        ],
    )
    def test_timestamp_report_configure(self, name, value, expected):
        self._configure_and_run(name, value, expected)

    @pytest.mark.parametrize(
        "name, value, expected",
        [
            ("", "", "Provided param '' for report 'timestamp' does not exist"),
            ("BAD", "", "Provided param 'BAD' for report 'timestamp' does not exist"),
            ("timezone", "BAD", "Provided timezone 'BAD' for report 'timestamp' is not valid."),
        ],
    )
    def test_timestamp_configure_invalid(self, name, value, expected):
        with pytest.raises(ConfigGeneralError) as err:
            report = TimestampReport()
            report.configure(name, value)
            report.get_report()
        assert expected in str(err)

    @pytest.mark.parametrize(
        "name, value, expected",
        [
            ("format", "", r".*([0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2})"),
        ],
    )
    def test_timestamp_default_warning(self, name, value, expected):
        with pytest.warns(UserWarning):
            self._configure_and_run(name, value, expected)


    def _configure_and_run(self, name, value, expected):
        report = TimestampReport()
        report.configure(name, value)
        assert re.search(expected, report.get_report())
