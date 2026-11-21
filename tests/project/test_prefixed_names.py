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


def test_call_matching_several_prefix_splits_is_ambiguous(tmp_path):
    """``a.b.Keyword`` matches both ``b.Keyword`` in ``a.resource`` and ``Keyword`` in ``a.b.resource``."""
    (tmp_path / "a.resource").write_text("*** Keywords ***\nb.Keyword\n    No Operation\n")
    (tmp_path / "a.b.resource").write_text("*** Keywords ***\nKeyword\n    No Operation\n")
    (tmp_path / "suite.robot").write_text(
        "*** Settings ***\nResource    a.resource\nResource    a.b.resource\n\n\n"
        "*** Test Cases ***\nTest\n    a.b.Keyword\n"
    )
    assert reported(run(tmp_path, ["ambiguous-keyword-name"])) == ["suite.robot:8 ambiguous-keyword-name"]


def test_call_matching_single_prefix_split_is_not_ambiguous(tmp_path):
    (tmp_path / "a.resource").write_text("*** Keywords ***\nb.Keyword\n    No Operation\n")
    (tmp_path / "a.b.resource").write_text("*** Keywords ***\nOther\n    No Operation\n")
    (tmp_path / "suite.robot").write_text(
        "*** Settings ***\nResource    a.resource\nResource    a.b.resource\n\n\n"
        "*** Test Cases ***\nTest\n    a.b.Keyword\n    a.b.Other\n"
    )
    assert reported(run(tmp_path, ["ambiguous-keyword-name", "keyword-not-found"])) == []
