from __future__ import annotations

import ast
import difflib
import re
from functools import total_ordering
from re import Pattern
from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable

try:
    from rich.markup import escape
except ImportError:  # Fails on vendored-in LSP plugin
    escape = None  # type: ignore[assignment]

from robot.api.parsing import Comment, End, If, IfHeader, ModelVisitor, Token
from robot.parsing.model import Statement
from robot.utils.robotio import file_writer
from robot.version import VERSION as RF_VERSION


@total_ordering
class Version:
    def __init__(self, major: int, minor: int, fix: int):
        self.major = major
        self.minor = minor
        self.fix = fix

    @classmethod
    def parse(cls, raw_version: str) -> Version:
        version = re.search(r"(?P<major>[0-9]+)\.(?P<minor>[0-9]+)\.?(?P<fix>[0-9]+)*", raw_version)
        if version is None:
            raise ValueError(f"Invalid version string: {raw_version}")
        major = int(version.group("major"))
        minor = int(version.group("minor")) if version.group("minor") is not None else 0
        fix = int(version.group("fix")) if version.group("fix") is not None else 0
        return cls(major, minor, fix)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self.major == other.major and self.minor == other.minor and self.fix == other.fix

    def __lt__(self, other: Version) -> bool:
        if self.major != other.major:
            return self.major < other.major
        if self.minor != other.minor:
            return self.minor < other.minor
        return self.fix < other.fix

    def __hash__(self) -> int:
        return hash((self.major, self.minor, self.fix))

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.fix}"


ROBOT_VERSION = Version.parse(RF_VERSION)


def rf_supports_lang() -> bool:
    return ROBOT_VERSION.major >= 6


class StatementLinesCollector(ModelVisitor):  # type: ignore[misc]
    """Used to get a writeable presentation of a Robot Framework model."""

    def __init__(self, model: Statement) -> None:
        self.text = ""
        self.visit(model)

    def visit_Statement(self, node: Statement) -> None:  # noqa: N802
        for token in node.tokens:
            self.text += token.value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, StatementLinesCollector):
            return NotImplemented
        return other.text == self.text

    def __hash__(self) -> int:
        return hash(self.text)


def validate_regex(value: str | None) -> Pattern[str] | None:
    try:
        return re.compile(value) if value is not None else None
    except re.error:
        raise click.BadParameter("Not a valid regular expression") from None


def decorate_diff_with_color(contents: list[str]) -> list[str]:
    """Decorate diff lines with rich console styles."""
    lines = []
    for line in contents:
        style = None
        if line.startswith(("+++", "---")):
            style = "bold"
        elif line.startswith("@@"):
            style = "cyan"
        elif line.startswith("+"):
            style = "green"
        elif line.startswith("-"):
            style = "red"
        if escape is not None:
            line = escape(line)
        if style:
            line = f"[{style}]{line}"
        lines.append(line)
    return lines


def escape_rich_markup(lines: list[str]) -> list[str]:
    if escape is not None:
        return [escape(line) for line in lines]
    return lines  # type: ignore[unreachable]


def normalize_name(name: str) -> str:
    return name.lower().replace("_", "").replace(" ", "")


def after_last_dot(name: str) -> str:
    return name.split(".")[-1]


def round_to_four(number: int) -> int:
    div = number % 4
    if div:
        return number + 4 - div
    return number


def any_non_sep(tokens: list[Token]) -> bool:
    return any(token.type not in (Token.EOL, Token.SEPARATOR, Token.EOS) for token in tokens)


def tokens_by_lines(node: Statement) -> Generator[list[Token], None, None]:
    for line in node.lines:
        if not any_non_sep(line):
            continue
        if line:
            if line[0].type == Token.VARIABLE:
                if line[0].value:
                    line[0].value = line[0].value.lstrip()
                else:
                    # if variable is prefixed with spaces
                    line = line[1:]
            elif line[0].type == Token.ARGUMENT:
                line[0].value = line[0].value.strip() if line[0].value else line[0].value
        yield [token for token in line if token.type not in (Token.SEPARATOR, Token.EOS)]


def left_align(node: Statement) -> Statement:
    """Remove leading separator token"""
    tokens = list(node.tokens)
    if tokens:
        tokens[0].value = tokens[0].value.lstrip(" \t")
    return Statement.from_tokens(tokens)


class RecommendationFinder:
    def find_similar(self, name: str, candidates: list[str]) -> str:
        norm_name = name.lower()
        norm_cand = self.get_normalized_candidates(candidates)
        matches = self.find(norm_name, list(norm_cand.keys()))
        if not matches:
            return ""
        matches = self.get_original_candidates(matches, norm_cand)
        if len(matches) == 1 and matches[0] == name:
            return ""
        suggestion = " Did you mean:\n"
        suggestion += "\n".join(f"    {match}" for match in matches)
        return suggestion

    def find(self, name: str, candidates: list[str], max_matches: int = 2) -> list[str]:
        """Return a list of close matches to `name` from `candidates`."""
        if not name or not candidates:
            return []
        cutoff = self._calculate_cutoff(name)
        return difflib.get_close_matches(name, candidates, n=max_matches, cutoff=cutoff)

    @staticmethod
    def _calculate_cutoff(string: str, min_cutoff: float = 0.5, max_cutoff: float = 0.85, step: float = 0.03) -> float:
        """
        Calculate cutoff.

        The longer the string the bigger required cutoff.
        """
        cutoff = min_cutoff + len(string) * step
        return min(cutoff, max_cutoff)

    @staticmethod
    def get_original_candidates(candidates: list[str], norm_candidates: dict[str, list[str]]) -> list[str]:
        """Map found normalized candidates to unique original candidates."""
        return sorted({c for cand in candidates for c in norm_candidates[cand]})

    @staticmethod
    def get_normalized_candidates(candidates: list[str]) -> dict[str, list[str]]:
        norm_cand = {cand.lower(): [cand] for cand in candidates}
        # most popular typos
        norm_cand["align"] = ["AlignSettingsSection", "AlignVariablesSection"]
        norm_cand["normalize"] = [
            "NormalizeAssignments",
            "NormalizeNewLines",
            "NormalizeSectionHeaderName",
            "NormalizeSeparators",
            "NormalizeSettingName",
        ]
        norm_cand["order"] = ["OrderSettings", "OrderSettingsSection"]
        norm_cand["alignsettings"] = ["AlignSettingsSection"]
        norm_cand["alignvariables"] = ["AlignVariablesSection"]
        norm_cand["assignmentnormalizer"] = ["NormalizeAssignments"]
        return norm_cand


class ModelWriter(ModelVisitor):  # type: ignore[misc]
    def __init__(self, output: str, newline: str) -> None:
        self.writer = file_writer(output, newline=newline)
        self.close_writer = True

    def write(self, model: Statement) -> None:
        try:
            self.visit(model)
        finally:
            if self.close_writer:
                self.writer.close()

    def visit_Statement(self, statement: Statement) -> None:  # noqa: N802
        for token in statement.tokens:
            self.writer.write(token.value)


class TestTemplateFinder(ast.NodeVisitor):
    def __init__(self) -> None:
        self.templated = False

    def visit_TestTemplate(self, node: ast.AST) -> None:
        if hasattr(node, "value") and node.value:
            self.templated = True


def is_suite_templated(node: Statement) -> bool:
    template_finder = TestTemplateFinder()
    template_finder.visit(node)
    return template_finder.templated


def is_blank_multiline(statements: list[Token]) -> bool:
    return (
        statements[0].type == Token.CONTINUATION
        and len(statements) == 3
        and statements[1].type == "ARGUMENT"
        and not statements[1].value
    )


def create_statement_from_tokens(statement: type[Statement], tokens: Iterable[Token], indent: Token) -> Statement:
    return statement([indent, Token(statement.type), *tokens])


def wrap_in_if_and_replace_statement(node: Statement, statement: type[Statement], default_separator: str) -> Statement:
    if len(node.data_tokens) < 2:
        return node
    condition = node.data_tokens[1]
    separator = Token(Token.SEPARATOR, default_separator)
    indent = Token(Token.SEPARATOR, node.tokens[0].value + default_separator)
    merged_comment = merge_comments_into_one(node.tokens)
    data_tokens = join_tokens_with_token(node.data_tokens[2:], separator)
    if data_tokens:
        data_tokens.insert(0, separator)
    if merged_comment:
        data_tokens.append(Token(Token.SEPARATOR, "  "))
        data_tokens.append(merged_comment)
    data_tokens.append(Token(Token.EOL))
    body = create_statement_from_tokens(statement=statement, tokens=data_tokens, indent=indent)
    header = IfHeader(
        [
            node.tokens[0],
            Token(Token.IF),
            separator,
            condition,
            Token(Token.EOL),
        ]
    )
    end = End.from_params(indent=node.tokens[0].value)
    return If(header=header, body=[body], orelse=None, end=end)


def get_comments(tokens: list[Token]) -> list[Token]:
    prev_sep = ""
    comments = []
    for token in tokens:
        if token.type == Token.COMMENT:
            if token.value.startswith("#"):
                comments.append(token)
            elif comments:
                comments[-1] = Token(Token.COMMENT, comments[-1].value + prev_sep + token.value)
            else:
                comments.append(Token(Token.COMMENT, f"# {token.value}"))
        elif token.type == Token.SEPARATOR:
            prev_sep = token.value
    return comments


def merge_comments_into_one(tokens: list[Token]) -> Token | None:
    comments = [token.value.lstrip("#").strip() for token in tokens if token.type == Token.COMMENT]
    if not comments:
        return None
    comment = " ".join(comments)
    return Token(Token.COMMENT, f"# {comment}")


def collect_comments_from_tokens(tokens: list[Token], indent: Token | None) -> list[Comment]:
    comments = get_comments(tokens)
    eol = Token(Token.EOL)
    if indent:
        return [Comment([indent, comment, eol]) for comment in comments]
    return [Comment([comment, eol]) for comment in comments]


def flatten_multiline(tokens: list[Token], separator: str, remove_comments: bool = False) -> list[Token]:
    flattened = []
    skip_start = False
    for tok in tokens[:-1]:
        if tok.type == Token.EOL:
            skip_start = True
        elif skip_start:
            if tok.type == Token.CONTINUATION:
                skip_start = False
        else:
            if tok.type == Token.ARGUMENT and tok.value == "":
                flattened.append(Token(Token.SEPARATOR, separator))
                tok.value = "${EMPTY}"
            if remove_comments and tok.type == Token.COMMENT:
                if flattened and flattened[-1].type == Token.SEPARATOR:
                    flattened.pop()
            else:
                flattened.append(tok)
    flattened.append(tokens[-1])
    return flattened


def split_on_token_type(tokens: list[Token], token_type: str) -> tuple[list[Token], list[Token]]:
    """Split list of tokens into two lists on token with token_type type."""
    for index, token in enumerate(tokens):
        if token.type == token_type:
            return tokens[:index], tokens[index:]
    return tokens, []


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


def join_tokens_with_token(tokens: list[Token], token: Token) -> list[Token]:
    """Insert token between every token in tokens list."""
    joined = [token] * (len(tokens) * 2 - 1)
    joined[0::2] = tokens
    return joined


def is_token_value_in_tokens(value: str, tokens: list[Token]) -> bool:
    return any(value == token.value for token in tokens)


def get_new_line(indent: Token | None = None) -> list[Token]:
    if indent:
        return [Token(Token.EOL), indent, Token(Token.CONTINUATION)]
    return [Token(Token.EOL), Token(Token.CONTINUATION)]


def is_var(value: str) -> bool:
    return len(value) > 3 and value.startswith("${") and value.endswith("}")


def get_line_length(tokens: list[Token]) -> int:
    return sum(len(token.value) for token in tokens)


def get_line_length_with_sep(tokens: list[Token], sep_len: int) -> int:
    return get_line_length(tokens) + ((len(tokens) - 1) * sep_len)


def join_comments(comments: list[Token]) -> list[Token]:
    tokens: list[Token] = []
    separator = Token(Token.SEPARATOR, "  ")
    for token in comments:
        tokens.append(separator)
        tokens.append(token)
    return tokens
