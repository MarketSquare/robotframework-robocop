"""Tests for applying fixes reported by the project level rules."""

from __future__ import annotations

from pathlib import Path

import pytest

from robocop.run import check_files

CUSTOM_RULES = str(Path(__file__).parent / "project_fix_rules.py")
SOURCE = "*** Test Cases ***\nTest\n    Old Keyword\n    Old Keyword    argument\n"
FIXED = "*** Test Cases ***\nTest\n    New Keyword\n    New Keyword    argument\n"


@pytest.fixture
def project(tmp_path):
    (tmp_path / "test.robot").write_text(SOURCE)
    return tmp_path


def run(source, root=None, **kwargs):
    return check_files(
        sources=[source],
        select=["renamed-keyword"],
        custom_rules=[CUSTOM_RULES],
        root=root or source,
        ignore_file_config=True,
        return_result=True,
        cache=False,
        silent=True,
        **kwargs,
    )


class TestProjectFixes:
    def test_issues_are_reported_without_fix(self, project):
        diagnostics = run(project)

        assert len(diagnostics) == 2
        assert (project / "test.robot").read_text() == SOURCE

    def test_fix_is_applied_and_saved(self, project):
        diagnostics = run(project, fix=True)

        assert (project / "test.robot").read_text() == FIXED
        assert diagnostics == []  # issues are fixed, so they are not reported anymore

    def test_diff_does_not_modify_the_file(self, project):
        run(project, diff=True)

        assert (project / "test.robot").read_text() == SOURCE

    def test_file_outside_of_the_selected_paths_is_not_fixed(self, project):
        """Project context is built from the whole project, but only selected files are fixed."""
        other = project / "other.robot"
        other.write_text(SOURCE)

        run(project / "test.robot", root=project, fix=True)

        assert (project / "test.robot").read_text() == FIXED
        assert other.read_text() == SOURCE

    def test_file_level_fixes_are_not_lost(self, project):
        """Both file level and project level rules fix the same file in one run."""
        (project / "test.robot").write_text(SOURCE.replace("Test Cases ***", "Test Cases ***  "))

        check_files(
            sources=[project],
            select=["renamed-keyword", "trailing-whitespace"],
            custom_rules=[CUSTOM_RULES],
            root=project,
            ignore_file_config=True,
            return_result=True,
            cache=False,
            silent=True,
            fix=True,
        )

        assert (project / "test.robot").read_text() == FIXED
