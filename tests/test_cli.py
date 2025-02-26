"""Test CLI commands / options common for linter and formatter."""

from typer.testing import CliRunner

from robocop import __version__
from robocop.cli import app


def test_version():
    runner = CliRunner()
    result = runner.invoke(app, ["--version"])
    assert result.stdout == f"robocop, version {__version__}\n"
