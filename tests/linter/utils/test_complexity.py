"""Unit tests for the complexity calculator used by the CPX rules."""

from __future__ import annotations

import inspect
import sys
import textwrap

import pytest
from robot.api import get_model

from robocop.linter.utils.complexity import ComplexityResult, compute_complexity, count_boolean_sequences

try:
    from robot.api.parsing import Group
except ImportError:  # RF < 7.2
    Group = None


MIXED_CONTROL_FLOW = """
[Arguments]    ${items}    ${mode}
FOR    ${item}    IN    @{items}
    IF    $mode == 'a'
        IF    $item > 10
            Log    big
        ELSE IF    $item > 5
            Log    medium
        ELSE
            Log    small
        END
    ELSE IF    $mode == 'b' and $item != 0
        WHILE    $item > 0    limit=10
            ${item}=    Evaluate    $item - 1
            IF    $item == 3    BREAK
        END
    END
END
TRY
    Risky Keyword
EXCEPT    ValueError*    type=glob
    Log    value error
EXCEPT    AS    ${err}
    Log    ${err}
FINALLY
    Log    done
END
"""


def keyword_complexity(body: str) -> ComplexityResult:
    """Parse a keyword whose body is ``body`` (4-space indented by this helper) and compute its complexity."""
    indented = textwrap.indent(textwrap.dedent(body).strip("\n"), "    ")
    model = get_model(f"*** Keywords ***\nKw\n{indented}\n")
    return compute_complexity(model.sections[0].body[0])


class TestCountBooleanSequences:
    @pytest.mark.parametrize(
        ("condition", "expected"),
        [
            (None, 0),
            ("", 0),
            ("$a", 0),
            ("$a and $b", 1),
            ("$a and $b and $c", 1),
            ("$a and $b or $c", 2),
            ("a or b and c or d", 3),
            ("($a or $b) and $c", 2),
            ("not $a and $b", 1),
            ("${a} and ${b}", 1),
            ("${x} == 'and or'", 0),
            ('${x} == "a" or ${y.attr} == "b"', 1),
            ("'unterminated and", 0),
            ("${unclosed and $b", 0),
            ("$a.attr == 'x' or $b['key']", 1),
            ("%{HOME} and $b or ${c}", 2),
            ("$a and 'unterminated", 0),
            ("($a and $b) == ($c and $d)", 2),
            ("f($a and $b, $c and $d)", 2),
            ("$a and ($b or $c)", 2),
            ("($a and $b) and $c", 1),
            ("not ($a and $b) or $c", 2),
        ],
    )
    def test_counts_runs_of_like_operators(self, condition: str | None, expected: int) -> None:
        assert count_boolean_sequences(condition) == expected


class TestComplexity:
    @pytest.mark.parametrize(
        ("body", "cyclomatic", "cognitive"),
        [
            pytest.param("Log    x", 1, 0, id="no-control-flow"),
            pytest.param(
                """
                IF    $a
                    Log    x
                END
                """,
                2,
                1,
                id="if",
            ),
            pytest.param(
                """
                IF    $a
                    Log    x
                ELSE IF    $b
                    Log    y
                ELSE
                    Log    z
                END
                """,
                3,
                3,
                id="if-elseif-else",
            ),
            pytest.param("IF    $a    Log    x", 2, 1, id="inline-if"),
            pytest.param(
                "IF    $a    Log    x    ELSE IF    $b    Log    y    ELSE    Log    z", 3, 3, id="inline-chain"
            ),
            pytest.param(
                """
                FOR    ${i}    IN RANGE    10
                    Log    ${i}
                END
                """,
                2,
                1,
                id="for",
            ),
            pytest.param(
                """
                WHILE    $a and $b    limit=5
                    Log    x
                END
                """,
                2,
                2,
                id="while-with-boolean",
            ),
            pytest.param(
                """
                IF    $a
                    IF    $b
                        IF    $c
                            Log    x
                        END
                    END
                END
                """,
                4,
                6,
                id="nested-ifs",
            ),
            pytest.param(
                """
                IF    $a    Log    x
                IF    $b    Log    y
                IF    $c    Log    z
                """,
                4,
                3,
                id="sequential-ifs",
            ),
            pytest.param(
                """
                IF    $a and $b or $c
                    Log    x
                END
                """,
                2,
                3,
                id="if-with-mixed-booleans",
            ),
            pytest.param(
                """
                FOR    ${i}    IN    @{items}
                    IF    $i    BREAK
                    IF    not $i    CONTINUE
                END
                """,
                4,
                5,
                id="break-continue-free",
            ),
            pytest.param(
                """
                TRY
                    IF    $a    Log    x
                EXCEPT    Error
                    Log    y
                END
                """,
                3,
                2,
                id="try-body-not-nested",
            ),
            pytest.param(
                """
                TRY
                    Log    x
                EXCEPT    A
                    IF    $a    Log    y
                EXCEPT    B
                    Log    z
                ELSE
                    IF    $b    Log    w
                FINALLY
                    IF    $c    Log    v
                END
                """,
                6,
                8,
                id="try-full",
            ),
            pytest.param("Run Keyword If    $a    Log    x", 2, 1, id="run-keyword-if"),
            pytest.param(
                "BuiltIn.Run Keyword If    $a    Log    x    ELSE IF    $b    Log    y    ELSE    Log    z",
                3,
                3,
                id="run-keyword-if-chain",
            ),
            pytest.param("Run Keyword Unless    $a    Log    x", 2, 1, id="run-keyword-unless"),
            pytest.param("${v}    Set Variable If    $a    1", 2, 1, id="set-variable-if"),
            pytest.param("${v}    Set Variable If    $a    1    $b    2    3", 3, 3, id="set-variable-if-chain"),
            pytest.param("Skip If    $a", 2, 1, id="skip-if"),
            pytest.param("Should Be True    $a", 1, 0, id="assertion-not-counted"),
            pytest.param("Given Run Keyword If    $a    Log    x", 2, 1, id="bdd-run-keyword-if"),
            pytest.param("When BuiltIn.Skip If    $a", 2, 1, id="bdd-library-prefixed"),
            pytest.param("Given Log    x", 1, 0, id="bdd-ordinary-keyword"),
            pytest.param("Run Keyword If    $a and $b or $c    Log    x", 2, 3, id="run-keyword-if-booleans"),
            pytest.param(
                "Run Keyword If    $a    Log    x    ELSE IF    $b and $c    Log    y",
                3,
                3,
                id="run-keyword-if-else-if-booleans",
            ),
            pytest.param(
                "${v}    Set Variable If    $a or $b    1    $c and $d    2    3", 3, 5, id="set-variable-if-booleans"
            ),
            pytest.param("Skip If    $a and $b", 2, 2, id="skip-if-booleans"),
            pytest.param("Run Keyword If    $a    Log    x and y", 2, 1, id="keyword-arguments-not-scanned"),
            pytest.param("Run Keyword If    $flag    Log    yes    ELSE    Log    ELSE", 2, 2, id="else-as-argument"),
            pytest.param(
                "Run Keyword If    $a    Log    x    ELSE IF    $b    Log    ELSE    ELSE    Log    z",
                3,
                3,
                id="else-as-argument-after-else-if",
            ),
            pytest.param(
                "Run Keyword If    $a    Log    ELSE    ELSE IF    $b    Log    y", 3, 2, id="else-if-takes-priority"
            ),
            pytest.param("Run Keyword If    $a    ELSE    x", 2, 1, id="keyword-named-like-marker"),
            pytest.param(
                """
                FOR    ${i}    IN    @{items}
                    Run Keyword If    $i    Log    x
                END
                """,
                3,
                3,
                id="conditional-keyword-nesting",
            ),
        ],
    )
    def test_scores(self, body: str, cyclomatic: int, cognitive: int) -> None:
        result = keyword_complexity(body)
        assert (result.cyclomatic, result.cognitive) == (cyclomatic, cognitive)

    @pytest.mark.skipif(Group is None, reason="GROUP requires Robot Framework 7.2+")
    def test_group_adds_no_nesting(self) -> None:
        result = keyword_complexity(
            """
            GROUP    Setup
                IF    $a    Log    x
            END
            """
        )
        assert (result.cyclomatic, result.cognitive) == (2, 1)

    def test_increments_explain_score(self) -> None:
        result = keyword_complexity(
            """
            IF    $a
                FOR    ${i}    IN    @{items}
                    Log    ${i}
                END
            END
            """
        )
        assert [(inc.lineno, inc.cognitive, inc.kind, inc.nesting) for inc in result.increments] == [
            (3, 1, "IF", 0),
            (4, 2, "FOR", 1),
        ]

    def test_mixed_control_flow(self) -> None:
        result = keyword_complexity(MIXED_CONTROL_FLOW)
        assert (result.cyclomatic, result.cognitive) == (10, 19)

    def test_test_case_is_supported(self) -> None:
        model = get_model("*** Test Cases ***\nT\n    IF    $a    Log    x\n")
        result = compute_complexity(model.sections[0].body[0])
        assert (result.cyclomatic, result.cognitive) == (2, 1)


class TestEdgeCases:
    @pytest.mark.parametrize(
        ("body", "cyclomatic", "cognitive"),
        [
            pytest.param(
                "${x}=    IF    $a    Set Variable    1    ELSE    Set Variable    2", 2, 2, id="inline-if-assign"
            ),
            pytest.param(
                """
                FOR    ${i}    IN    @{items}
                    IF    $i    RETURN
                END
                """,
                3,
                3,
                id="inline-if-return-in-for",
            ),
            pytest.param(
                """
                WHILE    $a    limit=3    on_limit=pass
                    Log    x
                END
                """,
                2,
                1,
                id="while-options",
            ),
            pytest.param(
                """
                IF    $a
                    Log    x
                ELSE IF    $a and $b or $c
                    Log    y
                END
                """,
                3,
                4,
                id="else-if-booleans",
            ),
            pytest.param("VAR    ${x}    1    scope=TEST", 1, 0, id="var"),
            pytest.param("[Documentation]    nothing", 1, 0, id="no-body"),
            pytest.param("Run Keyword If    @{args}", 2, 1, id="run-keyword-if-list-variable"),
            pytest.param("${x}    Set Variable If    $a", 2, 1, id="set-variable-if-condition-only"),
        ],
    )
    def test_rare_syntax(self, body: str, cyclomatic: int, cognitive: int) -> None:
        result = keyword_complexity(body)
        assert (result.cyclomatic, result.cognitive) == (cyclomatic, cognitive)

    @pytest.mark.skipif(Group is None, reason="GROUP requires Robot Framework 7.2+")
    def test_group_keeps_enclosing_nesting(self) -> None:
        result = keyword_complexity(
            """
            IF    $a
                GROUP    g
                    IF    $b    Log    x
                END
            END
            """
        )
        assert (result.cyclomatic, result.cognitive) == (3, 3)

    @pytest.mark.parametrize(
        "body",
        [
            pytest.param("IF    $a\n    Log    x", id="if-without-end"),
            pytest.param("IF\n    Log    x\nEND", id="if-without-condition"),
            pytest.param("ELSE\nLog    x", id="stray-else"),
            pytest.param("ELSE IF    $a\nLog    x", id="stray-else-if"),
            pytest.param("EXCEPT    x\nLog    x", id="stray-except"),
            pytest.param("END", id="stray-end"),
            pytest.param("TRY\n    Log    x\nEND", id="try-without-except"),
            pytest.param("FOR    ${i}    IN    a\n    Log    x", id="for-without-end"),
            pytest.param("WHILE\n    Log    x\nEND", id="while-without-condition"),
            pytest.param("${x}=", id="assignment-only"),
            pytest.param("${x}    Set Variable If", id="set-variable-if-without-arguments"),
        ],
    )
    def test_invalid_syntax_does_not_crash(self, body: str) -> None:
        result = keyword_complexity(body)
        assert result.cyclomatic >= 1
        assert result.cognitive >= 0

    def test_long_branch_chains_do_not_recurse(self) -> None:
        """ELSE IF / EXCEPT chains are walked iteratively, so they do not depend on the recursion limit."""
        branches = 150
        else_ifs = "".join(f"ELSE IF    $a == {i}\n    Log    {i}\n" for i in range(1, branches))
        excepts = "".join(f"EXCEPT    error {i}\n    Log    {i}\n" for i in range(branches))
        body = f"IF    $a == 0\n    Log    0\n{else_ifs}END\nTRY\n    Log    x\n{excepts}END"
        indented = textwrap.indent(body, "    ")
        keyword = get_model(f"*** Keywords ***\nKw\n{indented}\n").sections[0].body[0]
        original_limit = sys.getrecursionlimit()
        sys.setrecursionlimit(len(inspect.stack(0)) + 100)
        try:
            result = compute_complexity(keyword)
        finally:
            sys.setrecursionlimit(original_limit)
        assert result.cyclomatic == 1 + branches + branches


class TestContributors:
    def test_cognitive_contributors_are_top_lines(self) -> None:
        result = keyword_complexity(MIXED_CONTROL_FLOW)
        assert result.cognitive_contributors() == (
            "line 16 +4 (inline IF at nesting 3), line 6 +3 (IF at nesting 2), line 14 +3 (WHILE at nesting 2)"
        )

    def test_cognitive_contributors_merge_increments_of_one_line(self) -> None:
        result = keyword_complexity(
            """
            IF    $a
                Log    x
            ELSE IF    $a and $b
                Log    y
            END
            """
        )
        assert result.cognitive_contributors(limit=5) == "line 5 +2 (ELSE IF, boolean operators), line 3 +1 (IF)"

    def test_cyclomatic_contributors_count_decision_points(self) -> None:
        result = keyword_complexity(MIXED_CONTROL_FLOW)
        assert result.cyclomatic_contributors() == "2 IF, 2 ELSE IF, 2 EXCEPT, 1 FOR, 1 WHILE, 1 inline IF"

    def test_conditional_keywords_use_canonical_names(self) -> None:
        result = keyword_complexity(
            """
            BuiltIn.Run Keyword If    $a    Log    x    ELSE IF    $b    Log    y
            run keyword if    $c    Log    z
            """
        )
        assert result.cyclomatic_contributors() == "2 Run Keyword If, 1 Run Keyword If ELSE IF"

    def test_no_contributors(self) -> None:
        result = keyword_complexity("Log    x")
        assert (result.cyclomatic_contributors(), result.cognitive_contributors()) == ("none", "none")
