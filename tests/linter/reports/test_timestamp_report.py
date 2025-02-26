import re

import pytest

from robocop.linter.exceptions import ConfigGeneralError
from robocop.linter.reports.timestamp_report import TimestampReport
from robocop.linter.rules import Diagnostic


class TestTimestampReport:
    def test_timestamp_report(self, rule, config):
        report = TimestampReport(config)
        issue = Diagnostic(
            rule=rule,
            source="some/path/file.robot",
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
    def test_timestamp_report_configure(self, name, value, expected, config):
        self._configure_and_run(name, value, expected, config)

    @pytest.mark.parametrize(
        ("name", "value", "expected"),
        [
            ("", "", "Provided param '' for report 'timestamp' does not exist"),
            ("BAD", "", "Provided param 'BAD' for report 'timestamp' does not exist"),
        ],
    )
    def test_timestamp_configure_invalid(self, name, value, expected, config):
        report = TimestampReport(config)
        with pytest.raises(ConfigGeneralError) as err:
            report.configure(name, value)
        assert expected in str(err)

    def test_invalid_timestamp_report(self, config):
        report = TimestampReport(config)
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
    def test_timestamp_default_warning(self, name, value, expected, config):
        with pytest.warns(UserWarning):
            self._configure_and_run(name, value, expected, config)

    @staticmethod
    def _configure_and_run(name, value, expected, config):
        report = TimestampReport(config)
        report.configure(name, value)
        assert re.search(expected, report.get_report())
