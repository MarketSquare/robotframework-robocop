"""Reporting of the complexity rules on very long branch chains."""

import inspect
import sys
import textwrap
from types import SimpleNamespace

import pytest
from robot.api import get_model

from robocop.linter.rules.complexity import _report_if_too_complex

BRANCHES = 150


@pytest.mark.parametrize(
    ("header", "branch"),
    [
        pytest.param("IF    $a == 0", "ELSE IF    $a == {index}", id="else-if-chain"),
        pytest.param("TRY", "EXCEPT    error {index}", id="except-chain"),
    ],
)
def test_report_does_not_recurse_through_branch_chains(header: str, branch: str) -> None:
    lines = [header, "    Log    0"]
    for index in range(1, BRANCHES):
        lines.extend((branch.format(index=index), f"    Log    {index}"))
    lines.append("END")
    body = textwrap.indent("\n".join(lines), "    ")
    keyword = get_model(f"*** Keywords ***\nKw\n{body}\n").sections[0].body[0]
    reported: dict[str, object] = {}
    rule = SimpleNamespace(enabled=True, report=lambda **kwargs: reported.update(kwargs))
    original_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(len(inspect.stack(0)) + 100)
    try:
        _report_if_too_complex(rule, keyword, complexity=2, allowed=1, contributors=str)
    finally:
        sys.setrecursionlimit(original_limit)
    assert reported["extended_disablers"] == (2, 3 + 2 * BRANCHES)
