from __future__ import annotations

from typing import TYPE_CHECKING

from robocop.linter.utils.misc import normalize_robot_name

if TYPE_CHECKING:
    from collections.abc import Generator

    from robot.parsing import Token
    from robot.parsing.model import Keyword


class RunKeywordVariant:
    def __init__(
        self, lib_name: str, name: str, resolve: int = 1, branches: list | None = None, split_on_and: bool = False
    ):
        self.lib_name = lib_name
        self.name = normalize_robot_name(name)
        self.full_name = f"{self.lib_name}.{self.name}"
        self.resolve = resolve
        self.branches = branches
        self.split_on_and = split_on_and


class RunKeywords(dict):
    def __init__(self, keywords: list[RunKeywordVariant]):
        normalized_keywords = {}
        for keyword_variant in keywords:
            normalized_keywords[keyword_variant.name] = keyword_variant
            normalized_keywords[keyword_variant.full_name] = keyword_variant
        super().__init__(normalized_keywords)

    def __setitem__(self, keyword_name: str, kw_variant: RunKeywordVariant):
        super().__setitem__(kw_variant.name, kw_variant)
        super().__setitem__(kw_variant.full_name, kw_variant)

    def __getitem__(self, keyword_name: str) -> RunKeywordVariant:
        normalized_name = normalize_robot_name(keyword_name)
        return super().__getitem__(normalized_name)

    def __contains__(self, keyword_name: str) -> bool:
        normalized_name = normalize_robot_name(keyword_name)
        return super().__contains__(normalized_name)

    def get(self, keyword_name: str) -> RunKeywordVariant | None:
        normalized_name = normalize_robot_name(keyword_name)
        return super().get(normalized_name, None)

    def __missing__(self, keyword_name: str):
        return None


RUN_KEYWORDS = RunKeywords(
    [
        RunKeywordVariant("builtin", "Run Keyword"),
        RunKeywordVariant("builtin", "Run Keyword And Continue On Failure"),
        RunKeywordVariant("builtin", "Run Keyword And Expect Error", resolve=2),
        RunKeywordVariant("builtin", "Run Keyword And Ignore Error"),
        RunKeywordVariant("builtin", "Run Keyword And Return"),
        RunKeywordVariant("builtin", "Run Keyword And Return If", resolve=2),
        RunKeywordVariant("builtin", "Run Keyword And Return Status"),
        RunKeywordVariant("builtin", "Run Keyword And Warn On Failure"),
        RunKeywordVariant("builtin", "Run Keyword If", resolve=2, branches=["ELSE IF", "ELSE"]),
        RunKeywordVariant("builtin", "Run Keyword If All Tests Passed"),
        RunKeywordVariant("builtin", "Run Keyword If Any Tests Failed"),
        RunKeywordVariant("builtin", "Run Keyword If Test Failed"),
        RunKeywordVariant("builtin", "Run Keyword If Test Passed"),
        RunKeywordVariant("builtin", "Run Keyword If Timeout Occurred"),
        RunKeywordVariant("builtin", "Run Keyword Unless", resolve=2),
        RunKeywordVariant("builtin", "Run Keywords", split_on_and=True),
        RunKeywordVariant("builtin", "Repeat Keyword", resolve=2),
        RunKeywordVariant("builtin", "Wait Until Keyword Succeeds", resolve=3),
        RunKeywordVariant("pabotlib", "Run Setup Only Once"),
        RunKeywordVariant("pabotlib", "Run Teardown Only Once"),
        RunKeywordVariant("pabotlib", "Run Only Once"),
        RunKeywordVariant("pabotlib", "Run On Last Process"),
    ]
)


def skip_leading_tokens(tokens: list[Token], break_token: str) -> list[Token]:
    for index, token in enumerate(tokens):
        if token.type == break_token:
            return tokens[index:]
    return tokens


def is_token_value_in_tokens(value: str, tokens: list[Token]) -> bool:
    return any(value == token.value for token in tokens)


def split_on_token_value(tokens: list[Token], value: str, resolve: int) -> tuple[list[Token], list[Token], list[Token]]:
    """
    Split list of tokens into three lists based on token value.

    Returns tokens before found token, found token + `resolve` number of tokens, remaining tokens.
    """
    for index, token in enumerate(tokens):
        if value == token.value:
            prefix = tokens[:index]
            branch = tokens[index : index + resolve]
            remainder = tokens[index + resolve :]
            return prefix, branch, remainder
    return [], [], tokens


def iterate_keyword_names(keyword_node: Keyword, name_token_type: str) -> Generator[Token, None, None]:
    tokens = skip_leading_tokens(keyword_node.data_tokens, name_token_type)
    yield from parse_run_keyword(tokens)


def parse_run_keyword(tokens: list[Token]) -> Generator[Token, None, None]:
    if not tokens:
        return
    yield tokens[0]
    run_keyword = RUN_KEYWORDS[tokens[0].value]
    if not run_keyword:
        return
    tokens = tokens[run_keyword.resolve :]
    if run_keyword.branches:
        if "ELSE IF" in run_keyword.branches:
            while is_token_value_in_tokens("ELSE IF", tokens):
                prefix, branch, tokens = split_on_token_value(tokens, "ELSE IF", 2)
                yield from parse_run_keyword(prefix)
        if "ELSE" in run_keyword.branches and is_token_value_in_tokens("ELSE", tokens):
            prefix, branch, tokens = split_on_token_value(tokens, "ELSE", 1)
            yield from parse_run_keyword(prefix)
            yield from parse_run_keyword(tokens)
            return
    elif run_keyword.split_on_and:
        yield from split_on_and(tokens)
        return
    yield from parse_run_keyword(tokens)


def split_on_and(tokens: list[Token]) -> Generator[Token, None, None]:
    if not is_token_value_in_tokens("AND", tokens):
        yield from (token for token in tokens)
        return
    while is_token_value_in_tokens("AND", tokens):
        prefix, branch, tokens = split_on_token_value(tokens, "AND", 1)
        yield from parse_run_keyword(prefix)
    yield from parse_run_keyword(tokens)


def is_run_keyword(token_name: str) -> bool:
    run_keyword = RUN_KEYWORDS[token_name]
    return run_keyword is not None
