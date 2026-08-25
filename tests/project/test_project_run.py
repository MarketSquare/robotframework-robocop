"""Tests for running project level rules as a part of the ``check`` command."""

from __future__ import annotations

import pytest

from robocop.run import check_files


@pytest.fixture
def project(tmp_path):
    (tmp_path / "test.robot").write_text(
        "*** Test Cases ***\nTest\n    Used Keyword\n\n"
        "*** Keywords ***\nUsed Keyword\n    Log    message\n\nNot Used Keyword\n    Log    message\n"
    )
    return tmp_path


def run(source, select, **kwargs):
    return check_files(
        sources=[source],
        select=select,
        root=source,
        ignore_file_config=True,
        return_result=True,
        cache=False,
        silent=True,
        **kwargs,
    )


def rule_names(diagnostics):
    return sorted({diagnostic.rule.name for diagnostic in diagnostics})


class TestProjectRulesInCheck:
    def test_project_rule_is_run_when_selected(self, project):
        assert rule_names(run(project, ["unused-keyword"])) == ["unused-keyword"]

    def test_project_and_file_rules_are_reported_together(self, project):
        assert rule_names(run(project, ["unused-keyword", "missing-doc-test-case"])) == [
            "missing-doc-test-case",
            "unused-keyword",
        ]

    def test_project_rules_are_not_run_when_not_selected(self, project):
        assert rule_names(run(project, ["missing-doc-test-case"])) == ["missing-doc-test-case"]

    def test_no_project_skips_project_rules(self, project):
        assert run(project, ["unused-keyword"], project=False) == []

    def test_all_does_not_select_project_rules(self, project):
        assert "unused-keyword" not in rule_names(run(project, ["ALL"]))

    def test_all_with_project_selects_project_rules(self, project):
        assert "unused-keyword" in rule_names(run(project, ["ALL", "PROJECT"]))

    def test_no_project_keeps_file_rules(self, project):
        diagnostics = run(project, ["unused-keyword", "missing-doc-test-case"], project=False)
        assert rule_names(diagnostics) == ["missing-doc-test-case"]

    def test_project_flag_does_not_enable_disabled_rules(self, project):
        assert rule_names(run(project, ["missing-doc-test-case"], project=True)) == ["missing-doc-test-case"]

    def test_project_context_is_built_from_root(self, project):
        """Only one file is linted, but the context still knows about the whole project."""
        (project / "resource.resource").write_text("*** Keywords ***\nResource Keyword\n    Log    message\n")
        diagnostics = check_files(
            sources=[project / "test.robot"],
            select=["unused-keyword"],
            root=project,
            ignore_file_config=True,
            return_result=True,
            cache=False,
            silent=True,
        )
        assert len(diagnostics) == 2
