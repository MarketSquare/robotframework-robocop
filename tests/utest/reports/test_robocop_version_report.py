import pytest

from robocop.reports.robocop_version_report import RobocopVersionReport
from robocop.version import __version__


class TestRobocopVersionReport:
    @pytest.mark.parametrize("previous_results", [None, {}, {"generated_with": "3.4.0"}])
    @pytest.mark.parametrize("compare_runs", [True, False])
    def test_version_report(self, rule, compare_runs, previous_results):
        report = RobocopVersionReport(compare_runs=compare_runs)
        expected_message = f"\nReport generated by Robocop version: {__version__}"
        if previous_results and compare_runs:
            expected_message += ". Previous results generated by Robocop version: 3.4.0"
        assert report.get_report(previous_results) == expected_message

    @pytest.mark.parametrize("compare_runs", [True, False])
    def test_persistent_save(self, compare_runs, rule):
        report = RobocopVersionReport(compare_runs)
        expected = {"generated_with": __version__}
        results = report.persist_result()
        assert results == expected
