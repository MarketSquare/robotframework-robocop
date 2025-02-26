from unittest import mock

import pytest

from robocop.linter.reports.time_taken_report import TimeTakenReport


class TestTimeTakenReport:
    @pytest.mark.parametrize("previous_results", [None, {}, {"time_taken": "10.541"}])
    @pytest.mark.parametrize("compare_runs", [True, False])
    def test_version_report(self, rule, compare_runs, previous_results):
        mock_time = mock.Mock()
        mock_time.side_effect = [1.0, 4.541]
        with mock.patch("robocop.linter.reports.time_taken_report.timer", mock_time):
            report = TimeTakenReport(compare_runs=compare_runs)
            if previous_results and compare_runs:
                expected_message = "\nScan finished in 3.541s (-7.000)."
            else:
                expected_message = "\nScan finished in 3.541s."
            assert report.get_report(previous_results) == expected_message

    @pytest.mark.parametrize("previous_results", [None, {"time_taken": "10.541"}])  # previous is ignored in save
    @pytest.mark.parametrize("compare_runs", [True, False])  # saved even if compare is disabled
    @pytest.mark.parametrize(("get_report", "expected_time"), [(True, "2.000"), (False, "0.000")])
    def test_persistent_save(self, previous_results, compare_runs, get_report, expected_time):
        mock_time = mock.Mock()
        mock_time.side_effect = [1.0, 3.0]
        with mock.patch("robocop.linter.reports.time_taken_report.timer", mock_time):
            report = TimeTakenReport(compare_runs)
            if get_report:
                report.get_report(None)
            expected = {"time_taken": expected_time}
            results = report.persist_result()
            assert results == expected
