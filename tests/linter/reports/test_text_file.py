import os
import textwrap
from pathlib import Path

from robocop.linter.reports.text_file import TextFile
from tests import working_directory
from tests.linter.reports import generate_issues


class TestJSONReport:
    def test_configure_output_path(self, config, tmp_path):
        # arrange
        output_path = "path/to/file.txt"
        expected_path = tmp_path / output_path

        # act
        with working_directory(tmp_path):
            report = TextFile(config)
            report.configure("output_path", output_path)

        # assert
        assert report.output_path == Path(output_path)
        assert expected_path.parent.exists()

    def test_text_file_report(self, rule, rule2, tmp_path, config):
        # arrange
        expected_report = (
            textwrap.dedent("""
        tests/atest/rules/comments/ignored-data/test.robot:50:10 [W] 0101 Some description (some-message)
        tests/atest/rules/comments/ignored-data/test.robot:50:10 [E] 0902 Some description. Example (other-message)
        tests/atest/rules/misc/empty-return/test.robot:11:10 [E] 0902 Some description. Example (other-message)
        tests/atest/rules/misc/empty-return/test.robot:50:10 [W] 0101 Some description (some-message)""")
            .replace("/", os.path.sep)
            .lstrip()
        )
        issues = generate_issues(rule, rule2, tmp_path)

        # act
        report = TextFile(config)
        for issue in issues:
            report.add_message(issue)
        with working_directory(tmp_path):
            report.get_report()

        # assert
        actual_report = (tmp_path / "robocop.txt").read_text()
        assert actual_report == expected_report
