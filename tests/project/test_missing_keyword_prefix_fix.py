"""Tests for the fix of the ``missing-keyword-prefix`` rule."""

from __future__ import annotations

import pytest

from robocop.run import check_files

RESOURCE = """*** Keywords ***
Login
    [Arguments]    ${username}
    Log    ${username}

Logout
    Log    bye
"""
SOURCE = """*** Settings ***
Resource    login.resource

*** Test Cases ***
Test
    Login    user
    Given Logout
    login.Login    user
    Local Keyword

*** Keywords ***
Local Keyword
    Log    local
"""
FIXED = """*** Settings ***
Resource    login.resource

*** Test Cases ***
Test
    login.Login    user
    Given login.Logout
    login.Login    user
    Local Keyword

*** Keywords ***
Local Keyword
    Log    local
"""


@pytest.fixture
def project(tmp_path):
    (tmp_path / "login.resource").write_text(RESOURCE)
    (tmp_path / "test.robot").write_text(SOURCE)
    return tmp_path


def run(source, **kwargs):
    return check_files(
        sources=[source],
        select=["missing-keyword-prefix"],
        root=source,
        ignore_file_config=True,
        return_result=True,
        cache=False,
        silent=True,
        **kwargs,
    )


class TestMissingKeywordPrefixFix:
    def test_prefix_is_added(self, project):
        diagnostics = run(project, fix=True)

        assert (project / "test.robot").read_text() == FIXED
        assert diagnostics == []

    def test_diff_does_not_modify_the_file(self, project):
        run(project, diff=True)

        assert (project / "test.robot").read_text() == SOURCE
