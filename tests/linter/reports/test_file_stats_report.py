import pytest

from robocop.linter.diagnostics import Diagnostic
from robocop.linter.reports.file_stats_report import FileStatsReport


class TestFileStatReport:
    @pytest.mark.parametrize(
        ("previous_results", "files", "files_with_issues", "compare_runs", "output"),
        [
            (None, 0, set(), False, "\nNo files were processed."),
            ({}, 0, set(), False, "\nNo files were processed."),
            ({"files_count": 2, "files_with_issues": 0}, 0, set(), False, "\nNo files were processed."),
            (None, 0, set(), True, "\nNo files were processed."),
            ({}, 0, set(), True, "\nNo files were processed."),
            (
                {"files_count": 0, "files_with_issues": 0},
                0,
                set(),
                True,
                "\nNo files were processed. Previously 0 files were processed.",
            ),
            (
                {"files_count": 2, "files_with_issues": 2},
                0,
                set(),
                True,
                "\nNo files were processed. Previously 2 files were processed.",
            ),
            (None, 10, set(), True, "\nProcessed 10 files but no issues were found."),
            ({}, 10, set(), True, "\nProcessed 10 files but no issues were found."),
            (
                {"files_count": 2, "files_with_issues": 0},
                10,
                set(),
                True,
                "\nProcessed 10 (+8) files but no issues were found. Previously there were 0 files with issues.",
            ),
            (
                {"files_count": 2, "files_with_issues": 2},
                10,
                set(),
                True,
                "\nProcessed 10 (+8) files but no issues were found. Previously there were 2 files with issues.",
            ),
            (
                {"files_count": 2, "files_with_issues": 1},
                10,
                set(),
                True,
                "\nProcessed 10 (+8) files but no issues were found. Previously there was 1 file with issues.",
            ),
            (None, 10, set(), False, "\nProcessed 10 files but no issues were found."),
            ({}, 10, set(), False, "\nProcessed 10 files but no issues were found."),
            (
                {"files_count": 2, "files_with_issues": 0},
                10,
                set(),
                False,
                "\nProcessed 10 files but no issues were found.",
            ),
            (
                None,
                10,
                {"a.robot", "b.robot"},
                True,
                "\nProcessed 10 files from which 3 files contained issues.",
            ),
            (
                {},
                10,
                {"a.robot", "b.robot"},
                True,
                "\nProcessed 10 files from which 3 files contained issues.",
            ),
            (
                {"files_count": 2, "files_with_issues": 0},
                10,
                {"a.robot", "b.robot"},
                True,
                "\nProcessed 10 (+8) files from which 3 (+3) files contained issues.",
            ),
            (
                {"files_count": 10, "files_with_issues": 4},
                10,
                {"a.robot", "b.robot"},
                True,
                "\nProcessed 10 (+0) files from which 3 (-1) files contained issues.",
            ),
            (
                None,
                10,
                {"a.robot", "b.robot"},
                False,
                "\nProcessed 10 files from which 3 files contained issues.",
            ),
            (
                {},
                10,
                {"a.robot", "b.robot"},
                False,
                "\nProcessed 10 files from which 3 files contained issues.",
            ),
            (
                {"files_count": 10, "files_with_issues": 4},
                10,
                {"a.robot", "b.robot"},
                False,
                "\nProcessed 10 files from which 3 files contained issues.",
            ),
        ],
    )
    def test_file_stats_report(self, previous_results, files, files_with_issues, compare_runs, output, rule, config):
        config.linter.compare = compare_runs
        report = FileStatsReport(config)
        report.files_count = files
        report.files_with_issues = files_with_issues
        if files_with_issues:
            issue = Diagnostic(
                rule=rule,
                source="some/path/file.robot",
                node=None,
                lineno=50,
                col=10,
                end_lineno=None,
                end_col=None,
            )
            report.add_message(issue)
        assert report.get_report(previous_results) == output

    @pytest.mark.parametrize("compare_runs", [True, False])
    def test_persistent_save(self, compare_runs, rule, config):
        config.linter.compare = compare_runs
        report = FileStatsReport(config)
        report.files_count += 1
        for source in ("a.robot", "b.robot"):
            issue = Diagnostic(
                rule=rule,
                source=source,
                node=None,
                lineno=50,
                col=10,
                end_lineno=None,
                end_col=None,
            )
            report.add_message(issue)
        expected = {"files_count": 1, "files_with_issues": 2}
        results = report.persist_result()
        assert results == expected
