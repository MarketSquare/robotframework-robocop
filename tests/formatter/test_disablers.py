from pathlib import Path
from unittest.mock import Mock

import pytest
from robot.api import get_model

from robocop.formatter.disablers import DisabledLines, RegisterDisablers
from robocop.formatter.utils.misc import ROBOT_VERSION


@pytest.mark.parametrize(
    ("check_start", "check_end", "start_line", "end_line", "lines", "full_match", "expected"),
    [
        # only start/end line and no full_match
        (15, 30, 15, None, [], False, True),
        (15, 30, 15, 30, [], False, False),
        (14, 30, 15, 30, [], False, True),
        (15, 31, 15, 30, [], False, True),
        (15, 30, None, 30, [], False, False),
        (15, 30, None, None, [], False, False),
        (15, 30, 32, 50, [], False, True),
        # only start/end line and full_match
        (15, 30, 15, None, [], True, False),
        (15, 30, 15, 30, [], True, False),
        (14, 30, 15, 30, [], True, False),
        (15, 31, 15, 30, [], True, False),
        (15, 30, None, 30, [], True, False),
        (15, 30, None, None, [], True, False),
        (15, 30, 32, 50, [], True, True),
        # with lines (# robocop: fmt: off)
        (2, 5, None, None, [(2, 5), (10, 15)], False, True),
        (2, 5, None, None, [(2, 6), (10, 15)], False, True),
        (2, 5, None, None, [(1, 5), (10, 15)], False, True),
        (2, 5, None, None, [(3, 4), (10, 15)], False, True),
        (2, 5, None, None, [(10, 15)], False, False),
        (2, 5, 1, 6, [(2, 5), (10, 15)], False, True),
        (2, 5, 1, 6, [(10, 15)], False, False),
    ],
)
def test_is_node_disabled(check_start, check_end, start_line, end_line, lines, full_match, expected):
    disablers = DisabledLines(start_line, end_line, 99)
    disablers.parse_global_disablers()
    for start, end in lines:
        disablers.add_disabler(start, end)
    node = Mock()
    node.lineno = check_start
    node.end_lineno = check_end
    assert disablers.is_node_disabled(node, full_match=full_match) == expected


@pytest.mark.parametrize(
    ("test_file", "expected_lines", "file_disabled", "rf_version", "check_transformer"),
    [
        ("file_disabled.robot", [(1, 1), (14, 15)], True, 4, "all"),
        ("file_disabled_in_selected.robot", [(1, 1)], True, 4, "NormalizeNewLines"),
        ("file_disabled_in_selected.robot", [(14, 15)], False, 4, "all"),
        ("file_disabled_in_selected.robot", [], False, 4, "AlignTestCasesSection"),
        ("file_disabled_in_comments.robot", [(2, 4), (17, 18)], True, 4, "all"),
        ("file_disabled_in_comments_no_header.robot", [(2, 4), (17, 18)], True, 4, "all"),
        ("file_disabled_enabled_in_comments.robot", [(2, 6), (21, 22)], False, 4, "all"),
        ("file_disabled_and_enabled.robot", [(1, 2), (15, 16)], False, 4, "all"),
        ("test.robot", [(13, 14), (25, 37), (30, 33), (40, 41), (46, 48), (57, 58), (67, 67)], False, 5, "all"),
        ("open_disabler_in_section.robot", [(5, 8), (13, 15), (20, 23)], False, 4, "all"),
        ("empty.robot", [], False, 4, "all"),
    ],
)
def test_register_disablers(test_file, expected_lines, file_disabled, rf_version, check_transformer):
    if ROBOT_VERSION.major < rf_version:
        pytest.skip(f"Test enabled only for RF {rf_version}.*")
    test_file_path = Path(__file__).parent / "test_data" / "disablers" / test_file
    model = get_model(test_file_path)
    register_disablers = RegisterDisablers(None, None)
    register_disablers.visit(model)
    if check_transformer in register_disablers.disablers.disablers:
        assert register_disablers.disablers.disablers[check_transformer].lines == expected_lines
    assert register_disablers.is_disabled_in_file(check_transformer) == file_disabled
