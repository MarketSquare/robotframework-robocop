"""Test CLI commands / options common for linter and formatter."""

from typer.testing import CliRunner

from robocop import __version__
from robocop.cli import app


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
