"""Tests for associating arguments with nested keyword calls."""

from __future__ import annotations

from robot.api import Token, get_model

from robocop.parsing.run_keywords import iterate_keyword_calls


def keyword_calls(body: str) -> list[tuple[str, list[str]]]:
    """
    Parse test case body and return keyword calls with their arguments.

    Returns:
        List of tuples with keyword name and list of argument values.

    """
    source = f"*** Test Cases ***\nTest\n    {body}\n"
    model = get_model(source)
    calls: list[tuple[str, list[str]]] = []
    for node in model.sections[0].body[0].body:
        calls.extend(
            (call.name.value, [token.value for token in call.arguments])
            for call in iterate_keyword_calls(node, Token.KEYWORD)
        )
    return calls


class TestIterateKeywordCalls:
    def test_simple_call(self):
        assert keyword_calls("My Keyword    a    b") == [("My Keyword", ["a", "b"])]

    def test_call_without_arguments(self):
        assert keyword_calls("My Keyword") == [("My Keyword", [])]

    def test_run_keyword(self):
        assert keyword_calls("Run Keyword    My Keyword    a") == [
            ("Run Keyword", ["My Keyword", "a"]),
            ("My Keyword", ["a"]),
        ]

    def test_run_keyword_if_skips_condition(self):
        calls = keyword_calls("Run Keyword If    ${cond}    My Keyword    a    b")
        assert ("My Keyword", ["a", "b"]) in calls

    def test_run_keyword_if_else(self):
        calls = keyword_calls("Run Keyword If    ${cond}    First    a    ELSE    Second    b")
        assert ("First", ["a"]) in calls
        assert ("Second", ["b"]) in calls

    def test_run_keywords_without_and(self):
        calls = keyword_calls("Run Keywords    First    Second")
        assert ("First", []) in calls
        assert ("Second", []) in calls

    def test_run_keywords_with_and(self):
        calls = keyword_calls("Run Keywords    First    a    AND    Second    b    c")
        assert ("First", ["a"]) in calls
        assert ("Second", ["b", "c"]) in calls

    def test_wait_until_keyword_succeeds(self):
        calls = keyword_calls("Wait Until Keyword Succeeds    3x    1s    My Keyword    a")
        assert ("My Keyword", ["a"]) in calls
