"""Tests for resolving keyword calls in resource files through the namespace of the importing suites."""

from __future__ import annotations

from robocop.run import check_files

ORDERS_RESOURCE = """\
*** Keywords ***
Open Order
    Log Step    opening
    Not Defined In Any Importing Suite
"""

SUITE_DEFINING_LOG_STEP = """\
*** Settings ***
Resource    orders.resource


*** Test Cases ***
Order Flow
    Open Order


*** Keywords ***
Log Step
    [Arguments]    ${message}
    Log    ${message}
"""

SUITE_WITHOUT_LOG_STEP = """\
*** Settings ***
Resource    orders.resource


*** Test Cases ***
Order Flow
    Open Order
"""


def run(source):
    return check_files(
        sources=[source],
        select=["keyword-not-found"],
        root=source,
        ignore_file_config=True,
        return_result=True,
        cache=False,
        silent=True,
    )


def reported(diagnostics):
    return sorted(
        f"{diag.source.path.relative_to(diag.source.path.parents[1]).as_posix()}:{diag.range.start.line}"
        for diag in diagnostics
    )


def test_keyword_defined_in_importing_suite(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "orders.resource").write_text(ORDERS_RESOURCE)
    (project / "suite.robot").write_text(SUITE_DEFINING_LOG_STEP)
    assert reported(run(project)) == ["project/orders.resource:4"]


def test_keyword_defined_in_one_of_importing_suites(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "orders.resource").write_text(ORDERS_RESOURCE)
    (project / "a_suite.robot").write_text(SUITE_DEFINING_LOG_STEP)
    (project / "b_suite.robot").write_text(SUITE_WITHOUT_LOG_STEP)
    assert reported(run(project)) == ["project/orders.resource:4"]


def test_keyword_from_resource_higher_in_import_chain(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "common.resource").write_text(
        "*** Settings ***\nResource    api.resource\n\n\n*** Keywords ***\nCommon Step\n    No Operation\n"
    )
    (project / "api.resource").write_text("*** Settings ***\nResource    database.resource\n")
    (project / "database.resource").write_text("*** Keywords ***\nQuery Database\n    Common Step\n")
    (project / "suite.robot").write_text(
        "*** Settings ***\nResource    common.resource\n\n\n*** Test Cases ***\nQuery\n    Query Database\n"
    )
    assert reported(run(project)) == []


def test_resource_not_imported_by_any_suite(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "orders.resource").write_text(ORDERS_RESOURCE)
    assert reported(run(project)) == ["project/orders.resource:3", "project/orders.resource:4"]


def test_importing_suite_with_unresolved_import_is_not_checked(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "orders.resource").write_text(ORDERS_RESOURCE)
    (project / "suite.robot").write_text(
        "*** Settings ***\nResource    orders.resource\nResource    missing.resource\n\n\n"
        "*** Test Cases ***\nOrder Flow\n    Open Order\n"
    )
    assert reported(run(project)) == []
