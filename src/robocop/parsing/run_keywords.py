from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING

from robocop.linter.utils.misc import normalize_robot_name

if TYPE_CHECKING:
    from collections.abc import Generator

    from robot.api import Languages  # RF 6.0
    from robot.parsing import Token
    from robot.parsing.model import Keyword


class RunKeywordVariant:
    def __init__(
        self, lib_name: str, name: str, resolve: int = 1, branches: list[str] | None = None, split_on_and: bool = False
    ) -> None:
        self.lib_name = lib_name
        self.name = normalize_robot_name(name)
        self.full_name = f"{self.lib_name}.{self.name}"
        self.resolve = resolve
        self.branches = branches
        self.split_on_and = split_on_and


class RunKeywords(dict[str, RunKeywordVariant]):
    def __init__(self, keywords: list[RunKeywordVariant]) -> None:
        normalized_keywords: dict[str, RunKeywordVariant] = {}
        for keyword_variant in keywords:
            normalized_keywords[keyword_variant.name] = keyword_variant
            normalized_keywords[keyword_variant.full_name] = keyword_variant
        super().__init__(normalized_keywords)

    def __setitem__(self, keyword_name: str, kw_variant: RunKeywordVariant) -> None:
        super().__setitem__(kw_variant.name, kw_variant)
        super().__setitem__(kw_variant.full_name, kw_variant)

    def __getitem__(self, keyword_name: str) -> RunKeywordVariant:
        normalized_name = normalize_robot_name(keyword_name)
        return super().__getitem__(normalized_name)

    def __contains__(self, keyword_name: object) -> bool:
        if not isinstance(keyword_name, str):
            return False
        normalized_name = normalize_robot_name(keyword_name)
        return super().__contains__(normalized_name)

    def get(self, keyword_name: str, default: RunKeywordVariant | None = None) -> RunKeywordVariant | None:  # type: ignore[override]
        normalized_name = normalize_robot_name(keyword_name)
        return super().get(normalized_name, default)

    def __missing__(self, keyword_name: str) -> None:
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


BDD_PREFIXES = frozenset({"Given", "When", "Then", "And", "But"})
"""English BDD prefixes, used when no languages are configured (Robot Framework older than 6.0)."""


def bdd_prefixes_for(languages: Languages | None) -> frozenset[str]:
    """
    Return BDD prefixes of the given languages.

    Robot Framework's ``Languages`` contain English and every language enabled with the ``--language`` option or the
    ``Language:`` header of the file, so the result is the set of prefixes active in the file.

    Returns:
        Title-cased BDD prefixes, or the English prefixes if languages are not available.

    """
    prefixes = getattr(languages, "bdd_prefixes", None)  # RF 6.0+
    if not prefixes:
        return BDD_PREFIXES
    return frozenset(prefix.title() for prefix in prefixes)


@lru_cache(maxsize=32)
def _bdd_prefix_pattern(bdd_prefixes: frozenset[str]) -> re.Pattern[str]:
    """
    Build an alternation of the prefixes, the same way Robot Framework builds ``Languages.bdd_prefix_regexp``.

    Prefixes are tried from the longest one, words of a prefix are separated by any whitespace character and the case
    is compared with Unicode case folding rules of ``re.IGNORECASE``. Converting the name with ``str.lower`` or
    ``str.title`` instead is not equivalent: for example lowercase ``İ`` in Turkish ``DİYELİM Kİ`` is two characters.
    """
    prefixes = sorted(bdd_prefixes, key=len, reverse=True)
    alternatives = "|".join(re.escape(prefix).replace(r"\ ", r"\s") for prefix in prefixes)
    return re.compile(f"({alternatives})", re.IGNORECASE)


def get_bdd_prefix(name: str, bdd_prefixes: frozenset[str] = BDD_PREFIXES) -> str | None:
    """
    Return the BDD prefix the keyword name starts with.

    The prefix is matched like in Robot Framework: case-insensitively, the longest prefix first and only when it is
    followed by whitespace. Prefixes can contain several words, for example ``Étant donné que`` in French.

    Returns:
        The prefix as written in the name, or None if the name does not start with a BDD prefix.

    """
    match = _bdd_prefix_pattern(bdd_prefixes).match(name)
    if match is None or match.end() == len(name) or not name[match.end()].isspace():
        return None
    return match.group(1)


def is_bdd_prefix(name: str, bdd_prefixes: frozenset[str] = BDD_PREFIXES) -> bool:
    """
    Check if the whole name is a BDD prefix, for example a ``Given`` call without the keyword name.

    Returns:
        True if the name, with normalized whitespace, is one of the prefixes.

    """
    return _bdd_prefix_pattern(bdd_prefixes).fullmatch(" ".join(name.split())) is not None


def remove_bdd_prefix(name: str, bdd_prefixes: frozenset[str] = BDD_PREFIXES) -> str:
    """
    Remove the BDD prefix from the keyword name.

    Returns:
        Name without the prefix, or the original name if it does not start with one.

    """
    prefix = get_bdd_prefix(name, bdd_prefixes)
    if prefix is None:
        return name
    return name[len(prefix) :].lstrip()


def get_run_keyword(name: str, bdd_prefixes: frozenset[str] = BDD_PREFIXES) -> RunKeywordVariant | None:
    """
    Find the run keyword variant matching the name, ignoring the BDD prefix if there is one.

    Robot Framework resolves the full name first and only then retries without the BDD prefix,
    which is why ``Then Wait Until Keyword Succeeds`` runs the keyword passed in its arguments.

    Returns:
        Matching RunKeywordVariant or None if the name does not refer to a run keyword.

    """
    run_keyword = RUN_KEYWORDS.get(name)
    if run_keyword is not None:
        return run_keyword
    without_prefix = remove_bdd_prefix(name, bdd_prefixes)
    if without_prefix == name:
        return None
    return RUN_KEYWORDS.get(without_prefix)


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


def iterate_keyword_names(
    keyword_node: Keyword, name_token_type: str, bdd_prefixes: frozenset[str] = BDD_PREFIXES
) -> Generator[Token, None, None]:
    tokens = skip_leading_tokens(keyword_node.data_tokens, name_token_type)
    yield from parse_run_keyword(tokens, bdd_prefixes)


@dataclass
class KeywordCallTokens:
    """Keyword name token together with the argument tokens passed to that particular call."""

    name: Token
    arguments: list[Token]


def iterate_keyword_calls(
    keyword_node: Keyword, name_token_type: str, bdd_prefixes: frozenset[str] = BDD_PREFIXES
) -> Generator[KeywordCallTokens, None, None]:
    """
    Iterate over keyword calls in the statement, together with arguments of every call.

    Works like :func:`iterate_keyword_names`, but also returns arguments belonging to each keyword. It is required
    to validate the number of arguments used in nested keyword calls, such as ``Run Keyword If``, where arguments of
    the statement are not the arguments of the called keyword.

    Yields:
        KeywordCallTokens for every keyword call found in the statement.

    """
    tokens = skip_leading_tokens(keyword_node.data_tokens, name_token_type)
    yield from parse_run_keyword_calls(tokens, bdd_prefixes)


def parse_run_keyword_calls(
    tokens: list[Token], bdd_prefixes: frozenset[str] = BDD_PREFIXES
) -> Generator[KeywordCallTokens, None, None]:
    """
    Parse tokens into keyword calls, resolving nested run keywords.

    Yields:
        KeywordCallTokens for every keyword call found in the tokens.

    """
    if not tokens:
        return
    yield KeywordCallTokens(name=tokens[0], arguments=list(tokens[1:]))
    run_keyword = get_run_keyword(tokens[0].value, bdd_prefixes)
    if not run_keyword:
        return
    tokens = tokens[run_keyword.resolve :]
    if run_keyword.branches:
        if "ELSE IF" in run_keyword.branches:
            while is_token_value_in_tokens("ELSE IF", tokens):
                prefix, _branch, tokens = split_on_token_value(tokens, "ELSE IF", 2)
                yield from parse_run_keyword_calls(prefix, bdd_prefixes)
        if "ELSE" in run_keyword.branches and is_token_value_in_tokens("ELSE", tokens):
            prefix, _branch, tokens = split_on_token_value(tokens, "ELSE", 1)
            yield from parse_run_keyword_calls(prefix, bdd_prefixes)
            yield from parse_run_keyword_calls(tokens, bdd_prefixes)
            return
    elif run_keyword.split_on_and:
        yield from split_on_and_calls(tokens, bdd_prefixes)
        return
    yield from parse_run_keyword_calls(tokens, bdd_prefixes)


def split_on_and_calls(
    tokens: list[Token], bdd_prefixes: frozenset[str] = BDD_PREFIXES
) -> Generator[KeywordCallTokens, None, None]:
    """
    Split ``Run Keywords`` arguments into separate keyword calls.

    Without the ``AND`` separator every argument is a keyword name called without arguments.

    Yields:
        KeywordCallTokens for every keyword call found in the tokens.

    """
    if not is_token_value_in_tokens("AND", tokens):
        for token in tokens:
            yield KeywordCallTokens(name=token, arguments=[])
        return
    while is_token_value_in_tokens("AND", tokens):
        prefix, _branch, tokens = split_on_token_value(tokens, "AND", 1)
        yield from parse_run_keyword_calls(prefix, bdd_prefixes)
    yield from parse_run_keyword_calls(tokens, bdd_prefixes)


def parse_run_keyword(tokens: list[Token], bdd_prefixes: frozenset[str] = BDD_PREFIXES) -> Generator[Token, None, None]:
    if not tokens:
        return
    yield tokens[0]
    run_keyword = get_run_keyword(tokens[0].value, bdd_prefixes)
    if not run_keyword:
        return
    tokens = tokens[run_keyword.resolve :]
    if run_keyword.branches:
        if "ELSE IF" in run_keyword.branches:
            while is_token_value_in_tokens("ELSE IF", tokens):
                prefix, _branch, tokens = split_on_token_value(tokens, "ELSE IF", 2)
                yield from parse_run_keyword(prefix, bdd_prefixes)
        if "ELSE" in run_keyword.branches and is_token_value_in_tokens("ELSE", tokens):
            prefix, _branch, tokens = split_on_token_value(tokens, "ELSE", 1)
            yield from parse_run_keyword(prefix, bdd_prefixes)
            yield from parse_run_keyword(tokens, bdd_prefixes)
            return
    elif run_keyword.split_on_and:
        yield from split_on_and(tokens, bdd_prefixes)
        return
    yield from parse_run_keyword(tokens, bdd_prefixes)


def split_on_and(tokens: list[Token], bdd_prefixes: frozenset[str] = BDD_PREFIXES) -> Generator[Token, None, None]:
    if not is_token_value_in_tokens("AND", tokens):
        yield from (token for token in tokens)
        return
    while is_token_value_in_tokens("AND", tokens):
        prefix, _branch, tokens = split_on_token_value(tokens, "AND", 1)
        yield from parse_run_keyword(prefix, bdd_prefixes)
    yield from parse_run_keyword(tokens, bdd_prefixes)


def is_run_keyword(token_name: str) -> bool:
    return get_run_keyword(token_name) is not None
