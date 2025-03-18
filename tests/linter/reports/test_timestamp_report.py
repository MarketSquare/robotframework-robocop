import re

import pytest

from robocop.errors import ConfigurationError
from robocop.linter.reports.timestamp_report import TimestampReport


class TestTimestampReport:
    def test_timestamp_report(self, config, capsys):
        report = TimestampReport(config)
        report.generate_report()
        out, _ = capsys.readouterr()
        assert "Reported: " in out

    @pytest.mark.parametrize(
        ("name", "value", "expected"),
        [
            ("timezone", "UTC", r"\+0000"),
            ("format", "hello", r"Reported: hello"),
            ("format", "%Y-%m-%dT%H:%M:%S", r".*([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2})"),
        ],
    )
    def test_timestamp_report_configure(self, name, value, expected, config, capsys):
        self._configure_and_run(name, value, config)
        out, _ = capsys.readouterr()
        assert re.search(expected, out)

    @pytest.mark.parametrize(
        ("name", "value", "expected"),
        [
            ("", "", "Provided param '' for report 'timestamp' does not exist"),
            ("BAD", "", "Provided param 'BAD' for report 'timestamp' does not exist"),
        ],
    )
    def test_timestamp_configure_invalid(self, name, value, expected, config):
        report = TimestampReport(config)
        with pytest.raises(ConfigurationError) as err:
            report.configure(name, value)
        assert expected in str(err)

    def test_invalid_timestamp_report(self, config):
        report = TimestampReport(config)
        report.configure("timezone", "BAD")
        with pytest.raises(ConfigurationError) as err:
            report.generate_report()
        assert "Provided timezone 'BAD' for report 'timestamp' is not valid." in str(err)

    @pytest.mark.parametrize(
        ("name", "value", "expected"),
        [
            ("format", "", r".*([0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2})"),
        ],
    )
    def test_timestamp_default_warning(self, name, value, expected, config, capsys):
        with pytest.warns(UserWarning):
            self._configure_and_run(name, value, config)
        out, _ = capsys.readouterr()
        assert re.search(expected, out)

    @staticmethod
    def _configure_and_run(name, value, config):
        report = TimestampReport(config)
        report.configure(name, value)
        report.generate_report()
