from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from robocop import exceptions
from robocop.linter.reports import get_reports, is_custom_report_source, load_all_reports
from robocop.run import app
from tests import working_directory

TEST_DATA_DIR = Path(__file__).parent / "test_data"
CUSTOM_REPORTS_DIR = TEST_DATA_DIR / "custom_reports"
CUSTOM_REPORT_FILE = CUSTOM_REPORTS_DIR / "custom_report.py"


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("all", False),
        ("None", False),
        ("sarif", False),
        ("print_issues", False),
        ("custom_reports.custom_report", True),
        ("path/to/reports", True),
        ("path\\to\\reports", True),
        ("reports.py", True),
    ],
)
def test_is_custom_report_source(name, expected):
    assert is_custom_report_source(name) == expected


@pytest.mark.parametrize("source", [CUSTOM_REPORTS_DIR, CUSTOM_REPORT_FILE])
def test_load_custom_report_from_path(source, empty_config):
    empty_config.linter.reports = [str(source)]
    reports = get_reports(empty_config)
    assert "custom_report" in reports
    assert "print_issues" in reports  # default reports are still loaded


def test_custom_report_is_listed_in_all_reports(empty_config):
    empty_config.linter.reports = [str(CUSTOM_REPORT_FILE)]
    assert "custom_report" in load_all_reports(empty_config)


def test_load_custom_report_with_other_reports(empty_config):
    empty_config.linter.reports = [f"{CUSTOM_REPORT_FILE},timestamp"]
    reports = get_reports(empty_config)
    assert "custom_report" in reports
    assert "timestamp" in reports


def test_custom_reports_disabled_with_none(empty_config):
    empty_config.linter.reports = [str(CUSTOM_REPORT_FILE), "None"]
    reports = get_reports(empty_config)
    assert "custom_report" not in reports


def test_custom_report_order_is_preserved(empty_config):
    empty_config.linter.reports = ["all", str(CUSTOM_REPORT_FILE)]
    reports_list = list(get_reports(empty_config).keys())
    assert reports_list.index("timestamp") < reports_list.index("custom_report")
    empty_config.linter.reports = [str(CUSTOM_REPORT_FILE), "all"]
    reports_list = list(get_reports(empty_config).keys())
    assert reports_list.index("custom_report") < reports_list.index("timestamp")


def test_custom_report_with_existing_name(empty_config, tmp_path):
    report_source = tmp_path / "duplicated_report.py"
    report_source.write_text(
        "from robocop.linter.reports import Report\n\n\n"
        "class DuplicatedReport(Report):\n"
        "    def __init__(self, config):\n"
        "        self.name = 'timestamp'\n"
        "        self.description = 'Duplicated report'\n"
        "        super().__init__(config)\n"
    )
    empty_config.linter.reports = [str(report_source)]
    with pytest.raises(exceptions.ConfigurationError):
        get_reports(empty_config)


def test_custom_report_path_relative_to_config(tmp_path):
    shutil.copy(CUSTOM_REPORT_FILE, tmp_path / "custom_report.py")
    (tmp_path / "test.robot").write_text("*** Settings ***\n\n")
    (tmp_path / "robocop.toml").write_text('[tool.robocop.lint]\nreports = ["custom_report.py"]\n')
    runner = CliRunner()
    with working_directory(tmp_path):
        result = runner.invoke(app, ["check", "--no-cache"])
    assert "Custom report: found 4 issues" in result.output


def test_invalid_custom_report_source(empty_config, capsys):
    empty_config.linter.reports = ["idontexist.reports"]
    with pytest.raises(exceptions.InvalidCustomReportSource):
        get_reports(empty_config)
    _, err = capsys.readouterr()
    assert "Failed to load custom reports from" in err
    assert "'idontexist.reports'" in err


def test_check_with_custom_report(tmp_path):
    (tmp_path / "test.robot").write_text("*** Settings ***\n\n")
    runner = CliRunner()
    with working_directory(tmp_path):
        result = runner.invoke(app, ["check", "--no-cache", "--reports", str(CUSTOM_REPORT_FILE)])
    assert "Custom report: found 4 issues" in result.output


def test_configure_custom_report(tmp_path):
    (tmp_path / "test.robot").write_text("*** Settings ***\n\n")
    runner = CliRunner()
    with working_directory(tmp_path):
        result = runner.invoke(
            app,
            [
                "check",
                "--no-cache",
                "--reports",
                str(CUSTOM_REPORT_FILE),
                "--configure",
                "custom_report.prefix=Configured",
            ],
        )
    assert "Configured: found 4 issues" in result.output


def test_list_custom_report(tmp_path):
    runner = CliRunner()
    with working_directory(tmp_path):
        result = runner.invoke(app, ["list", "reports", "--reports", str(CUSTOM_REPORT_FILE)])
    assert "custom_report" in result.output
    assert "Example custom report" in result.output


def test_docs_for_custom_report(tmp_path):
    config_path = tmp_path / "robocop.toml"
    config_path.write_text(f'[tool.robocop.lint]\nreports = ["{CUSTOM_REPORT_FILE.as_posix()}"]\n')
    runner = CliRunner()
    with working_directory(tmp_path):
        result = runner.invoke(app, ["docs", "custom_report"])
    assert "Example custom report" in result.output
