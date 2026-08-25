"""Tests for the fix of the ``missing-argument-name`` rule."""

from __future__ import annotations

import pytest

from robocop.run import check_files

KEYWORDS = """*** Keywords ***
Login
    [Arguments]    ${username}    ${password}    ${remember}=False
    Log    ${username}
"""
SOURCE = """*** Settings ***
Resource    keywords.resource

*** Test Cases ***
Test
    Login    user    pwd
    Login    user    pwd=x    remember=True
"""
FIXED = """*** Settings ***
Resource    keywords.resource

*** Test Cases ***
Test
    Login    username=user    password=pwd
    Login    username=user    password=pwd=x    remember=True
"""


@pytest.fixture
def project(tmp_path):
    (tmp_path / "keywords.resource").write_text(KEYWORDS)
    (tmp_path / "test.robot").write_text(SOURCE)
    return tmp_path


def run(source, **kwargs):
    return check_files(
        sources=[source],
        select=["missing-argument-name"],
        root=source,
        ignore_file_config=True,
        return_result=True,
        cache=False,
        silent=True,
        **kwargs,
    )


class TestMissingArgumentNameFix:
    def test_all_arguments_in_the_line_are_fixed_at_once(self, project):
        diagnostics = run(project, fix=True)

        assert (project / "test.robot").read_text() == FIXED
        assert diagnostics == []

    def test_diff_does_not_modify_the_file(self, project):
        run(project, diff=True)

        assert (project / "test.robot").read_text() == SOURCE
