"""Tests for calls prefixed with the resource or library name, when the keyword name contains dots."""

from __future__ import annotations

from robocop.run import check_files

UTIL_RESOURCE = """\
*** Keywords ***
Wait 1.5 Seconds
    No Operation

Go To example.com
    No Operation

util.Nested Name
    No Operation
"""

SUITE = """\
*** Settings ***
Resource    util.resource


*** Test Cases ***
Dotted Names
    util.Wait 1.5 Seconds
    util.Go To example.com
    util.util.Nested Name
    util.Not Defined
"""


def run(source, select):
    return check_files(
        sources=[source],
        select=select,
        root=source,
        ignore_file_config=True,
        return_result=True,
        cache=False,
        silent=True,
    )


def reported(diagnostics):
    return sorted(f"{diag.source.path.name}:{diag.range.start.line} {diag.rule.name}" for diag in diagnostics)


def test_prefixed_keyword_with_dots_in_name(tmp_path):
    (tmp_path / "util.resource").write_text(UTIL_RESOURCE)
    (tmp_path / "suite.robot").write_text(SUITE)
    assert reported(run(tmp_path, ["keyword-not-found", "unused-keyword"])) == ["suite.robot:10 keyword-not-found"]


def test_prefixed_call_with_dots_validates_arguments(tmp_path):
    (tmp_path / "util.resource").write_text("*** Keywords ***\nGo To example.com\n    No Operation\n")
    (tmp_path / "suite.robot").write_text(
        "*** Settings ***\nResource    util.resource\n\n\n"
        "*** Test Cases ***\nTest\n    util.Go To example.com    extra\n"
    )
    assert reported(run(tmp_path, ["invalid-argument-count"])) == ["suite.robot:7 invalid-argument-count"]
