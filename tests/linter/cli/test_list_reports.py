from unittest.mock import MagicMock, patch

from robocop.cli import list_reports


class TestListReports:
    def test_list_reports(self, empty_linter, capsys):
        with patch("robocop.cli.RobocopLinter", MagicMock(return_value=empty_linter)):
            list_reports()
        out, _ = capsys.readouterr()
        first_line = out.split("\n")[0]
        assert first_line == "Available reports:"
        assert "version              - Returns Robocop version (disabled)" in out

    def test_list_reports_enabled_not_configured(self, empty_linter, capsys):
        with patch("robocop.cli.RobocopLinter", MagicMock(return_value=empty_linter)):
            list_reports(enabled=True)
        out, _ = capsys.readouterr()
        first_line = out.split("\n")[0]
        assert first_line == "No available reports that meet your search criteria."
        assert "version              - Returns Robocop version (disabled)" not in out

    def test_list_reports_enabled_configured_single(self, empty_linter, capsys):
        list_reports(enabled=True, reports=["version"])
        out, _ = capsys.readouterr()
        first_line = out.split("\n")[0]
        assert first_line == "Available reports:"
        assert "version              - Returns Robocop version (enabled)" in out
        assert "scan_timer           - Returns Robocop execution time (disabled)" not in out

    def test_list_reports_enabled_configured_all(self, empty_linter, capsys):
        list_reports(enabled=True, reports=["all"])
        out, _ = capsys.readouterr()
        first_line = out.split("\n")[0]
        assert first_line == "Available reports:"
        assert "version              - Returns Robocop version (enabled)" in out
        assert "scan_timer           - Returns Robocop execution time (enabled)" in out

    def test_list_reports_disabled_not_configured(self, empty_linter, capsys):
        list_reports(enabled=False)
        out, _ = capsys.readouterr()
        first_line = out.split("\n")[0]
        assert first_line == "Available reports:"
        assert "version              - Returns Robocop version (enabled)" not in out
        assert "version              - Returns Robocop version (disabled)" in out
        assert "sarif                - Generate SARIF output file (disabled - non-default)" in out

    def test_list_reports_disabled_configured_all(self, empty_linter, capsys):
        list_reports(enabled=False, reports=["all"])
        out, _ = capsys.readouterr()
        first_line = out.split("\n")[0]
        assert first_line == "Available reports:"
        assert "version              - Returns Robocop version (enabled)" not in out
        assert "sarif                - Generate SARIF output file (disabled - non-default)" in out
