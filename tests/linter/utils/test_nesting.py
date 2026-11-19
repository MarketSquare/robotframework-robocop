"""Unit tests for the nesting depth calculator used by the CPX nesting depth rules."""

from __future__ import annotations

import inspect
import sys
import textwrap

import pytest
from robot.api import Token, get_model

from robocop.linter.utils.nesting import find_deep_blocks, max_nesting_depth

try:
    from robot.api.parsing import Group
except ImportError:  # RF < 7.2
    Group = None

requires_group = pytest.mark.skipif(Group is None, reason="GROUP is supported from Robot Framework 7.2")


def parse_keyword(body: str):
    """Parse a keyword whose body is ``body`` (4-space indented by this helper). The first body line is line 3."""
    indented = textwrap.indent(textwrap.dedent(body).strip("\n"), "    ")
    return get_model(f"*** Keywords ***\nKw\n{indented}\n").sections[0].body[0]


class TestMaxNestingDepth:
    @pytest.mark.parametrize(
        ("body", "expected"),
        [
            pytest.param(
                """
                Log    x
                Log    y
                """,
                0,
                id="no-control-flow",
            ),
            pytest.param(
                """
                IF    $a
                    Log    x
                END
                """,
                1,
                id="if",
            ),
            pytest.param(
                """
                IF    $a
                    Log    a
                ELSE IF    $b
                    Log    b
                ELSE IF    $c
                    Log    c
                ELSE
                    Log    d
                END
                """,
                1,
                id="if-with-many-branches",
            ),
            pytest.param(
                """
                IF    $a
                    IF    $b
                        Log    x
                    END
                END
                """,
                2,
                id="nested-if",
            ),
            pytest.param("IF    $a    Log    x", 0, id="inline-if"),
            pytest.param("IF    $a    Log    x    ELSE IF    $b    Log    y    ELSE    Log    z", 0, id="inline-chain"),
            pytest.param("${x} =    IF    $a    Set Variable    1    ELSE    Set Variable    2", 0, id="inline-assign"),
            pytest.param(
                """
                IF    $a    Log    x
                IF    $b    Log    y
                IF    $c    Log    z
                """,
                0,
                id="sequential-inline",
            ),
            pytest.param(
                """
                IF    $a
                ...    Log    split
                ...    ELSE
                ...    Log    other
                """,
                0,
                id="inline-if-continuation-lines",
            ),
            pytest.param(
                """
                FOR    ${i}    IN    1
                    IF    $i    Log    x
                END
                """,
                1,
                id="inline-if-in-for",
            ),
            pytest.param(
                """
                FOR    ${i}    IN    1
                    IF    $i
                        Log    x
                    END
                END
                """,
                2,
                id="if-in-for",
            ),
            pytest.param(
                """
                FOR    ${i}    IN    1
                    FOR    ${j}    IN    1
                        Log    x
                    END
                END
                """,
                2,
                id="for-in-for",
            ),
            pytest.param(
                """
                FOR    ${i}    ${v}    IN ENUMERATE    a    b
                    Log    x
                END
                FOR    ${i}    IN RANGE    3
                    Log    x
                END
                FOR    ${a}    ${b}    IN ZIP    ${x}    ${y}
                    Log    x
                END
                """,
                1,
                id="for-variants-are-sequential",
            ),
            pytest.param(
                """
                FOR    ${i}    IN    1
                    WHILE    $i    limit=2    on_limit=PASS
                        Log    x
                    END
                END
                """,
                2,
                id="while-in-for",
            ),
            pytest.param(
                """
                TRY
                    Log    a
                EXCEPT    A
                    Log    b
                EXCEPT    B
                    Log    c
                ELSE
                    Log    d
                FINALLY
                    Log    e
                END
                """,
                1,
                id="try-with-all-branches",
            ),
            pytest.param(
                """
                IF    $a
                    TRY
                        Log    x
                    EXCEPT
                        Log    y
                    END
                END
                """,
                2,
                id="try-in-if",
            ),
            pytest.param(
                """
                IF    $a
                    Log    a
                ELSE IF    $b
                    IF    $c
                        Log    c
                    END
                ELSE
                    Log    d
                END
                """,
                2,
                id="if-in-else-if-branch",
            ),
            pytest.param(
                """
                IF    $a
                    Log    a
                ELSE
                    FOR    ${i}    IN    1
                        Log    x
                    END
                END
                """,
                2,
                id="for-in-else-branch",
            ),
            pytest.param(
                """
                TRY
                    Log    a
                EXCEPT
                    IF    $a
                        Log    b
                    END
                END
                """,
                2,
                id="if-in-except",
            ),
            pytest.param(
                """
                TRY
                    Log    a
                FINALLY
                    IF    $a
                        Log    b
                    END
                END
                """,
                2,
                id="if-in-finally",
            ),
            pytest.param(
                """
                TRY
                    Log    a
                EXCEPT    A
                    Log    b
                ELSE
                    FOR    ${i}    IN    1
                        Log    c
                    END
                END
                """,
                2,
                id="for-in-try-else",
            ),
            pytest.param(
                """
                FOR    ${order}    IN    1
                    IF    $order
                        TRY
                            IF    $order
                                Log    x
                            END
                        EXCEPT
                            Log    y
                        END
                    END
                END
                """,
                4,
                id="for-if-try-if",
            ),
            pytest.param(
                """
                FOR    ${i}    IN    1
                    IF    $i    BREAK
                    IF    $i    CONTINUE
                    IF    $i    RETURN
                END
                """,
                1,
                id="inline-guards",
            ),
            pytest.param(
                """
                FOR    ${i}    IN    1
                    Run Keyword If    $i    Log    x    ELSE    Log    y
                    Skip If    $i
                    Return From Keyword If    $i
                    Run Keyword And Return If    $i    Log    x
                END
                """,
                1,
                id="conditional-keywords",
            ),
            pytest.param(
                """
                FOR    ${i}    IN    1
                    VAR    ${x}    1
                    ${y} =    Set Variable    2
                END
                """,
                1,
                id="var-and-assignment",
            ),
        ],
    )
    def test_depth(self, body: str, expected: int) -> None:
        assert max_nesting_depth(parse_keyword(body)) == expected

    def test_tabs_and_mixed_indentation(self) -> None:
        source = (
            "*** Keywords ***\nKw\n"
            "\tFOR\t${a}\tIN\t1\n"
            "\t\tIF\t$a\n"
            "  Log  x\n"
            "\t\tEND\n"
            "\tEND\n"
            "  IF  $b\n"
            "      Log  y\n"
            "  END\n"
        )
        assert max_nesting_depth(get_model(source).sections[0].body[0]) == 2

    @requires_group
    @pytest.mark.parametrize(
        ("body", "expected"),
        [
            pytest.param(
                """
                GROUP    One
                    Log    x
                END
                """,
                0,
                id="group",
            ),
            pytest.param(
                """
                GROUP    One
                    IF    $a
                        Log    x
                    END
                END
                """,
                1,
                id="if-in-group",
            ),
            pytest.param(
                """
                GROUP    One
                    GROUP    Two
                        IF    $a
                            Log    x
                        END
                    END
                END
                """,
                1,
                id="if-in-nested-groups",
            ),
            pytest.param(
                """
                IF    $a
                    GROUP    One
                        FOR    ${i}    IN    1
                            Log    x
                        END
                    END
                END
                """,
                2,
                id="for-in-group-in-if",
            ),
            pytest.param(
                """
                GROUP    One
                    Log    a
                END
                GROUP    Two
                    Log    b
                END
                """,
                0,
                id="sequential-groups",
            ),
        ],
    )
    def test_group_is_transparent(self, body: str, expected: int) -> None:
        assert max_nesting_depth(parse_keyword(body)) == expected


class TestFindDeepBlocks:
    def test_nothing_reported_within_limit(self) -> None:
        keyword = parse_keyword(
            """
            FOR    ${i}    IN    1
                IF    $i
                    Log    x
                END
            END
            """
        )
        assert find_deep_blocks(keyword, max_depth=2) == []

    def test_reports_outermost_block_over_the_limit_with_deepest_path(self) -> None:
        keyword = parse_keyword(
            """
            FOR    ${a}    IN    1
                IF    $a
                    TRY
                        IF    $a
                            WHILE    $a
                                Log    x
                            END
                        END
                    EXCEPT
                        Log    y
                    END
                END
            END
            """
        )
        (block,) = find_deep_blocks(keyword, max_depth=2)
        assert block.node.lineno == 5  # the TRY: the first block over the limit
        assert block.token_type == Token.TRY
        assert block.depth == 5
        assert block.path_text == "FOR > IF > TRY > IF > WHILE"

    def test_reports_separate_blocks_independently(self) -> None:
        keyword = parse_keyword(
            """
            IF    $a
                IF    $b
                    Log    first
                END
            END
            FOR    ${i}    IN    1
                FOR    ${j}    IN    1
                    TRY
                        Log    second
                    END
                END
            END
            """
        )
        blocks = find_deep_blocks(keyword, max_depth=1)
        assert [(block.node.lineno, block.depth, block.path_text) for block in blocks] == [
            (4, 2, "IF > IF"),
            (9, 3, "FOR > FOR > TRY"),
        ]

    def test_branches_do_not_add_a_level(self) -> None:
        keyword = parse_keyword(
            """
            IF    $a
                Log    a
            ELSE IF    $b
                FOR    ${i}    IN    1
                    IF    $i
                        Log    b
                    END
                END
            ELSE
                Log    c
            END
            """
        )
        assert find_deep_blocks(keyword, max_depth=3) == []
        (block,) = find_deep_blocks(keyword, max_depth=2)
        assert block.path_text == "IF > FOR > IF"

    def test_blocks_in_all_branches_are_checked(self) -> None:
        keyword = parse_keyword(
            """
            TRY
                IF    $a
                    IF    $b
                        Log    x
                    END
                END
            EXCEPT
                FOR    ${i}    IN    1
                    IF    $i
                        WHILE    $i
                            Log    y
                        END
                    END
                END
            END
            """
        )
        blocks = find_deep_blocks(keyword, max_depth=2)
        assert [(block.node.lineno, block.path_text) for block in blocks] == [
            (5, "TRY > IF > IF"),
            (11, "TRY > FOR > IF > WHILE"),
        ]

    @pytest.mark.parametrize("token_type", [Token.IF, Token.FOR, Token.WHILE, Token.TRY])
    def test_header_token_of_each_block_type(self, token_type: str) -> None:
        headers = {
            Token.IF: "IF    $a",
            Token.FOR: "FOR    ${i}    IN    1",
            Token.WHILE: "WHILE    $a",
            Token.TRY: "TRY",
        }
        header = headers[token_type]
        keyword = parse_keyword(f"{header}\n    {header}\n        Log    x\n    END\nEND")
        (block,) = find_deep_blocks(keyword, max_depth=1)
        assert block.token_type == token_type
        assert block.node.header.get_token(token_type) is not None

    def test_long_branch_chains_do_not_recurse(self) -> None:
        """ELSE IF / EXCEPT chains are walked iteratively, so they do not depend on the recursion limit."""
        branches = 150
        else_ifs = "".join(f"ELSE IF    $a == {i}\n    Log    {i}\n" for i in range(1, branches))
        excepts = "".join(f"EXCEPT    error {i}\n    Log    {i}\n" for i in range(branches))
        tail = "ELSE\n    FOR    ${i}    IN    1\n        IF    $i\n            Log    deep\n        END\n    END\n"
        body = f"IF    $a == 0\n    Log    0\n{else_ifs}{tail}END\nTRY\n    Log    x\n{excepts}END"
        keyword = parse_keyword(body)
        original_limit = sys.getrecursionlimit()
        sys.setrecursionlimit(len(inspect.stack(0)) + 100)
        try:
            deepest = max_nesting_depth(keyword)
            blocks = find_deep_blocks(keyword, max_depth=1)
        finally:
            sys.setrecursionlimit(original_limit)
        assert deepest == 3
        assert [block.path_text for block in blocks] == ["IF > FOR > IF"]

    def test_invalid_blocks_do_not_fail(self) -> None:
        keyword = parse_keyword(
            """
            FOR    ${i}    IN    a
                IF    $i
                    WHILE    $i
                        TRY
            IF    $a
            """
        )
        assert max_nesting_depth(keyword) >= 1
        find_deep_blocks(keyword, max_depth=1)
