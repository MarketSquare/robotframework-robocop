import re

import pytest

from robocop.linter.exceptions import ConfigGeneralError
from robocop.linter.reports.timestamp_report import TimestampReport
from robocop.linter.rules import Message


class TestTimestampReport:
    @pytest.mark.parametrize("previous_results", [None, {}, {"issue": 10}])
    @pytest.mark.parametrize("compare_runs", [True, False])
    def test_timestamp_report(self, rule, compare_runs, previous_results):
        report = TimestampReport()
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
        assert "Reported: " in report.get_report()

    @pytest.mark.parametrize(
        ("name", "value", "expected"),
        [
            ("timezone", "UTC", r"\+0000"),
            ("format", "hello", r"Reported: hello"),
            ("format", "%Y-%m-%dT%H:%M:%S", r".*([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2})"),
        ],
    )
    def test_timestamp_report_configure(self, name, value, expected):
        self._configure_and_run(name, value, expected)

    @pytest.mark.parametrize(
        ("name", "value", "expected"),
        [
            ("", "", "Provided param '' for report 'timestamp' does not exist"),
            ("BAD", "", "Provided param 'BAD' for report 'timestamp' does not exist"),
        ],
    )
    def test_timestamp_configure_invalid(self, name, value, expected):
        report = TimestampReport()
        with pytest.raises(ConfigGeneralError) as err:
            report.configure(name, value)
        assert expected in str(err)

    def test_invalid_timestamp_report(self):
        report = TimestampReport()
        report.configure("timezone", "BAD")
        with pytest.raises(ConfigGeneralError) as err:
            report.get_report()
        assert "Provided timezone 'BAD' for report 'timestamp' is not valid." in str(err)

    @pytest.mark.parametrize(
        ("name", "value", "expected"),
        [
            ("format", "", r".*([0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2})"),
        ],
    )
    def test_timestamp_default_warning(self, name, value, expected):
        with pytest.warns(UserWarning):
            self._configure_and_run(name, value, expected)

    @staticmethod
    def _configure_and_run(name, value, expected):
        report = TimestampReport()
        report.configure(name, value)
        assert re.search(expected, report.get_report())
