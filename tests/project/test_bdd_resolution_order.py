"""Tests for the order in which a call with a BDD prefix is resolved."""

from __future__ import annotations

from robocop.run import check_files
from robocop.version_handling import ROBOT_VERSION, Version


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


BDD_ORDER_SUITE = """\
*** Test Cases ***
Prefixed Call
    Given Ready    with argument


*** Keywords ***
Given Ready
    No Operation

Ready
    [Arguments]    ${value}
    Log    ${value}
"""


class TestBddResolutionOrder:
    """Robot Framework 7.1+ tries the name without the BDD prefix first, older versions the full name."""

    def test_names_to_check_order(self, tmp_path):
        (tmp_path / "test.robot").write_text(BDD_ORDER_SUITE, encoding="utf-8")
        diagnostics = run(tmp_path, ["invalid-argument-count"])
        if ROBOT_VERSION >= Version("7.1"):  # noqa: SIM300
            assert reported(diagnostics) == []
        else:
            assert reported(diagnostics) == ["test.robot:3 invalid-argument-count"]
