"""Files are treated as suite initialization files only when Robot Framework does so (issue #2006)."""

import pytest

from robocop.run import check_files
from robocop.version_handling import ROBOT_VERSION

SUITE = "*** Test Cases ***\nLogin Works\n    Log    ok\n"


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


def test_suite_with_init_inside_name_is_ordinary_suite(tmp_path):
    (tmp_path / "login__init__flow.robot").write_text(SUITE, encoding="utf-8")
    assert reported(run(tmp_path, ["invalid-section", "empty-section"])) == []


@pytest.mark.skipif(
    ROBOT_VERSION.major < 6, reason="Robot Framework 5 parses test cases in initialization files as a comment section"
)
def test_init_file_with_test_cases_is_still_reported(tmp_path):
    (tmp_path / "__init__.robot").write_text(SUITE, encoding="utf-8")
    assert reported(run(tmp_path, ["invalid-section"])) == ["__init__.robot:1 invalid-section"]


def test_imports_of_suite_with_init_inside_name_are_not_shared(tmp_path):
    """Only imports of a real initialization file are treated as used by the other files in the directory."""
    (tmp_path / "steps.resource").write_text("*** Keywords ***\nStep\n    No Operation\n", encoding="utf-8")
    (tmp_path / "login__init__flow.robot").write_text(
        "*** Settings ***\nResource    steps.resource\n\n\n" + SUITE, encoding="utf-8"
    )
    (tmp_path / "other.robot").write_text(
        "*** Settings ***\nResource    steps.resource\n\n\n*** Test Cases ***\nTest\n    Step\n", encoding="utf-8"
    )
    assert reported(run(tmp_path, ["unused-resource-import"])) == ["login__init__flow.robot:2 unused-resource-import"]


def test_file_with_init_inside_name_can_be_resource_file(tmp_path):
    """A real initialization file without tests is fine, a suite file named ``suite__init__`` is not one."""
    (tmp_path / "__init__.robot").write_text("*** Keywords ***\nStep\n    No Operation\n", encoding="utf-8")
    (tmp_path / "suite__init__.robot").write_text("*** Keywords ***\nStep\n    No Operation\n", encoding="utf-8")
    assert reported(run(tmp_path, ["can-be-resource-file"])) == ["suite__init__.robot:1 can-be-resource-file"]
