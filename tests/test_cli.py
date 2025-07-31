"""Test CLI commands / options common for linter and formatter."""

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from robocop import __version__
from robocop.run import app
from tests import working_directory


def test_version():
    runner = CliRunner()
    result = runner.invoke(app, ["--version"])
    assert result.stdout == f"robocop, version {__version__}\n"


def test_print_docs_rule():
    runner = CliRunner()
    result = runner.invoke(app, ["docs", "line-too-long"])
    assert "Rule: line-too-long (LEN08)" in result.stdout


def test_print_docs_report():
    runner = CliRunner()
    result = runner.invoke(app, ["docs", "file_stats"])
    assert "Report that displays overall statistics about number of processed files." in result.stdout


def test_print_docs_formatter():
    runner = CliRunner()
    result = runner.invoke(app, ["docs", "NormalizeSeparators"])
    assert "All separators (pipes included) are converted to fixed length of 4 spaces " in result.stdout


def test_print_docs_invalid():
    runner = CliRunner()
    result = runner.invoke(app, ["docs", "idontexist"])
    assert result.exit_code == 2
    assert result.stdout == "There is no rule, formatter or a report with a 'idontexist' name.\n"


def test_invalid_threshold():
    runner = CliRunner()
    result = runner.invoke(app, ["check", "--threshold", "unknown"])
    assert result.exit_code == 2
    assert result.stdout == "ConfigurationError: Invalid severity value 'unknown'. Choose one from: I, W, E.\n"


class TestListFormatters:
    def test_list_formatters_default(self):
        runner = CliRunner()
        result = runner.invoke(app, ["list", "formatters"])
        assert result.exit_code == 0
        assert "NormalizeNewLines" in result.stdout
        assert "Translate" in result.stdout

    def test_list_enabled(self):
        runner = CliRunner()
        result = runner.invoke(app, ["list", "formatters", "--filter", "ENABLED"])
        assert result.exit_code == 0
        assert "NormalizeNewLines" in result.stdout
        assert "ReplaceReturns" in result.stdout
        assert "Translate" not in result.stdout

    def test_list_disabled(self):
        runner = CliRunner()
        result = runner.invoke(app, ["list", "formatters", "--filter", "DISABLED"])
        assert result.exit_code == 0
        assert "NormalizeNewLines" not in result.stdout
        assert "Translate" in result.stdout

    def test_target_version(self):
        runner = CliRunner()
        result = runner.invoke(app, ["list", "formatters", "--filter", "ENABLED", "--target-version", "4"])
        assert result.exit_code == 0
        assert "NormalizeNewLines" in result.stdout
        assert "ReplaceReturns" not in result.stdout

    def test_return_status(self, tmp_path):
        runner = CliRunner()
        with working_directory(tmp_path):
            result = runner.invoke(app, ["check", "--reports", "return_status"])
        assert result.exit_code == 0

    def test_file_reports(self, tmp_path):
        (tmp_path / "test.robot").write_text("*** Settings ***")
        runner = CliRunner()
        with working_directory(tmp_path):
            result = runner.invoke(app, ["check", "--reports", "gitlab,sarif,json_report,sonarqube,text_file"])
        assert result.exit_code == 1
        assert "Generated Gitlab Code Quality report at robocop-code-quality.json" in result.stdout
        assert "Generated SARIF report at .sarif.json" in result.stdout
        assert "Generated JSON report at robocop.json" in result.stdout
        assert "Generated SonarQube report at robocop_sonar_qube.json" in result.stdout

    @pytest.mark.parametrize(
        ("check", "will_format", "expected_exit_code"),
        [
            (False, True, 0),
            (False, False, 0),
            (True, True, 1),
            (True, False, 0),
        ],
    )
    def test_check_exit_code(self, check, will_format, expected_exit_code):
        test_data = Path(__file__).parent / "formatter" / "formatters" / "NormalizeSeparators"
        if will_format:
            test_data = test_data / "source"
        else:
            test_data = test_data / "expected"
        command = ["format", "--select", "NormalizeSeparators", "--no-overwrite"]
        if check:
            command += ["--check"]
        with working_directory(test_data):
            result = CliRunner().invoke(app, [*command, "test.robot"])
        assert result.exit_code == expected_exit_code

    @pytest.mark.parametrize(
        ("check", "overwrite", "will_write"),
        [(True, False, False), (False, False, True), (True, True, True), (False, True, True)],
    )
    def test_check_overwrite_mode(self, check, overwrite, will_write):
        test_data = Path(__file__).parent / "formatter" / "formatters" / "NormalizeNewLines" / "source"
        command = ["format", "--select", "NormalizeNewLines"]
        if check:
            command.append("--check")
        if overwrite:
            command.append("--overwrite")
        with patch("robocop.formatter.utils.misc.ModelWriter") as mock_writer, working_directory(test_data):
            result = CliRunner().invoke(app, [*command, "tests.robot"])
            if will_write:
                mock_writer.assert_called()
            else:
                mock_writer.assert_not_called()
            assert result.exit_code == int(check)

    @pytest.mark.parametrize("option_name", ["-e", "--exclude", "--default-exclude"])
    def test_exclude_paths_linter(self, option_name):
        test_data = Path(__file__).parent / "linter" / "rules" / "arguments" / "invalid_argument"
        with working_directory(test_data):
            result = CliRunner().invoke(app, ["check", option_name, "test.robot"])
        assert result.exit_code == 0

    @pytest.mark.parametrize("option_name", ["--include", "--default-include"])
    def test_include_empty_path_linter(self, option_name):
        test_data = Path(__file__).parent / "linter" / "rules" / "arguments" / "invalid_argument"
        with working_directory(test_data):
            result = CliRunner().invoke(app, ["check", option_name, "test2.robot", "-e", "test.robot"])
        assert result.exit_code == 0

    @pytest.mark.parametrize("option_name", ["-e", "--exclude", "--default-exclude"])
    def test_exclude_paths_formatter(self, option_name):
        test_data = Path(__file__).parent / "formatter" / "test_data" / "good_bad_files"
        with working_directory(test_data):
            result = CliRunner().invoke(app, ["format", "--no-overwrite", "--check", option_name, "bad.robot"])
        assert result.exit_code == 0

    @pytest.mark.parametrize("option_name", ["--include", "--default-include"])
    def test_include_empty_path_formatter(self, option_name):
        test_data = Path(__file__).parent / "formatter" / "test_data" / "good_bad_files"
        with working_directory(test_data):
            result = CliRunner().invoke(
                app, ["format", "--no-overwrite", "--check", option_name, "good.robot", "-e", "bad.robot"]
            )
        assert result.exit_code == 0
