from pathlib import Path
from unittest.mock import Mock

import pytest

from robocop.exceptions import ConfigurationError
from robocop.linter.diagnostics import Diagnostics
from robocop.linter.reports.gitlab import GitlabReport
from robocop.linter.reports.json_report import JsonReport
from robocop.linter.reports.sarif import SarifReport
from robocop.linter.reports.sonarqube import SonarQubeReport
from robocop.linter.reports.text_file import TextFile
from robocop.runtime.resolved_config import ResolvedConfig
from tests.linter.reports import generate_issues


def generate_file_report(report, diagnostics: Diagnostics) -> None:
    """Call ``generate_report`` with the arguments required by the given report."""
    if isinstance(report, SarifReport):
        config_manager = Mock()
        config_manager.root = Path.cwd()
        resolved_config = Mock(spec=ResolvedConfig)
        resolved_config.rules = {}
        report.generate_report(diagnostics, config_manager, resolved_config)
    elif isinstance(report, SonarQubeReport):
        config_manager = Mock()
        config_manager.root = Path.cwd()
        report.generate_report(diagnostics, config_manager)
    else:
        report.generate_report(diagnostics)


FILE_REPORTS = [GitlabReport, JsonReport, SarifReport, SonarQubeReport, TextFile]


class TestSkipOnEmpty:
    @pytest.mark.parametrize("report_class", FILE_REPORTS)
    def test_file_not_created_on_empty_results(self, report_class, empty_config, tmp_path):
        output_file = tmp_path / "reports" / "report.out"
        report = report_class(empty_config)
        report.configure("output_path", str(output_file))
        report.configure("skip_on_empty", "True")

        generate_file_report(report, Diagnostics([]))

        assert not output_file.exists()

    @pytest.mark.parametrize("report_class", FILE_REPORTS)
    def test_previous_file_is_not_overwritten(self, report_class, empty_config, tmp_path):
        output_file = tmp_path / "report.out"
        output_file.write_text("previous run")
        report = report_class(empty_config)
        report.configure("output_path", str(output_file))
        report.configure("skip_on_empty", "True")

        generate_file_report(report, Diagnostics([]))

        assert output_file.read_text() == "previous run"

    @pytest.mark.parametrize("report_class", FILE_REPORTS)
    def test_file_created_when_there_are_issues(self, report_class, empty_config, tmp_path, rule, rule2):
        output_file = tmp_path / "report.out"
        report = report_class(empty_config)
        report.configure("output_path", str(output_file))
        report.configure("skip_on_empty", "True")

        generate_file_report(report, Diagnostics(generate_issues(empty_config, rule, rule2)))

        assert output_file.exists()

    @pytest.mark.parametrize("report_class", FILE_REPORTS)
    def test_file_created_on_empty_results_by_default(self, report_class, empty_config, tmp_path):
        output_file = tmp_path / "report.out"
        report = report_class(empty_config)
        report.configure("output_path", str(output_file))

        generate_file_report(report, Diagnostics([]))

        assert output_file.exists()

    @pytest.mark.parametrize("report_class", FILE_REPORTS)
    def test_invalid_configuration(self, report_class, empty_config):
        report = report_class(empty_config)
        with pytest.raises(ConfigurationError):
            report.configure("skip_on_empy", "True")
