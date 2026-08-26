from __future__ import annotations

import ast
import difflib
import re
from typing import TYPE_CHECKING

import typer
from rich.markup import escape
from robot.api.parsing import (
    Comment,
    ElseHeader,
    ElseIfHeader,
    End,
    If,
    IfHeader,
    KeywordCall,
    ModelVisitor,
    Token,
)
from robot.parsing.model import Statement
from robot.utils.robotio import file_writer

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable


def validate_regex(value: str | None) -> re.Pattern[str] | None:
    try:
        return re.compile(value) if value is not None else None
    except re.error:
        raise typer.BadParameter("Not a valid regular expression") from None


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
        line = escape(line)
        if style:
            line = f"[{style}]{line}"
        lines.append(line)
    return lines


def escape_rich_markup(lines: list[str]) -> list[str]:
    return [escape(line) for line in lines]


def normalize_name(name: str) -> str:
    return name.lower().replace("_", "").replace(" ", "")


def after_last_dot(name: str) -> str:
    return name.split(".")[-1]


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
            "NormalizeNewLines",
            "NormalizeSectionHeaderName",
            "NormalizeSeparators",
            "NormalizeSettingName",
        ]
        norm_cand["order"] = ["OrderSettings", "OrderSettingsSection"]
        norm_cand["alignsettings"] = ["AlignSettingsSection"]
        norm_cand["alignvariables"] = ["AlignVariablesSection"]
        return norm_cand


class ModelWriter(ModelVisitor):  # type: ignore[misc] # TODO: potentially replace with get source_lines -> write to file
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


def _run_keyword_if_insert_separators(indent: str, tokens: list[Token], separator: str) -> Generator[Token, None, None]:
    yield Token(Token.SEPARATOR, indent)
    for token in tokens[:-1]:
        yield token
        yield Token(Token.SEPARATOR, separator)
    yield tokens[-1]
    yield Token(Token.EOL)


def _run_keyword_if_split_args(
    args: list[Token], delimiters: tuple[str, ...], assign: list[Token] | None = None
) -> Generator[list[Token], None, None]:
    split_points = [index for index, arg in enumerate(args) if arg.value in delimiters]
    prev_index = 0
    for split_point in split_points:
        yield args[prev_index:split_point]
        prev_index = split_point
    yield args[prev_index : len(args)]
    if assign and "ELSE" in delimiters and not any(arg.value == "ELSE" for arg in args):
        values = [Token(Token.ARGUMENT, "${None}")] * len(assign)
        yield [Token(Token.ELSE), Token(Token.ARGUMENT, "Set Variable"), *values]


def _run_keyword_if_useless_set_variable(tokens: list[Token], assign: list[Token]) -> bool:
    if not assign or normalize_name(tokens[0].value) != "setvariable" or len(tokens[1:]) != len(assign):
        return False
    return all(
        normalize_name(var.value) == normalize_name(var_assign.value)
        for var, var_assign in zip(tokens[1:], assign, strict=False)
    )


def _run_keyword_if_args_to_keyword(
    arg_tokens: list[Token], assign: list[Token], indent: str, separator: str
) -> KeywordCall:
    separated_tokens = list(
        _run_keyword_if_insert_separators(
            indent,
            [*assign, Token(Token.KEYWORD, arg_tokens[0].value), *arg_tokens[1:]],
            separator,
        )
    )
    return KeywordCall.from_tokens(separated_tokens)


def _run_keyword_if_create_keywords(
    arg_tokens: list[Token], assign: list[Token], indent: str, separator: str
) -> list[KeywordCall]:
    keyword_name = normalize_name(arg_tokens[0].value)
    if keyword_name == "runkeywords":
        return [
            _run_keyword_if_args_to_keyword(keyword[1:], assign, indent, separator)
            for keyword in _run_keyword_if_split_args(arg_tokens, ("AND",))
        ]
    if is_var(keyword_name):
        keyword_token = Token(Token.KEYWORD_NAME, "Run Keyword")
        arg_tokens = [keyword_token, *arg_tokens]
    return [_run_keyword_if_args_to_keyword(arg_tokens, assign, indent, separator)]


def run_keyword_if_to_branched(
    node: KeywordCall, separator: str, indent: str, negate: bool = False
) -> If | KeywordCall:
    """
    Convert a ``Run Keyword If`` (or ``Run Keyword Unless``) keyword call to an ``IF`` block.

    ``separator`` is the whitespace used between tokens, ``indent`` is the extra indentation added to the block body.
    When ``negate`` is set (``Run Keyword Unless``) the ``IF`` condition is wrapped in ``not (...)``.
    The original ``node`` is returned unchanged when it cannot be safely converted.
    """
    base_separator = node.tokens[0]
    assign = node.get_tokens(Token.ASSIGN)
    raw_args = node.get_tokens(Token.ARGUMENT)
    if len(raw_args) < 2:
        return node
    end = End([base_separator, Token(Token.END), Token(Token.EOL)])
    prev_if: If | None = None
    for branch in reversed(list(_run_keyword_if_split_args(raw_args, ("ELSE", "ELSE IF"), assign=assign))):
        if branch[0].value == "ELSE":
            if len(branch) < 2:
                return node
            args = branch[1:]
            if _run_keyword_if_useless_set_variable(args, assign):
                continue
            header = ElseHeader([base_separator, Token(Token.ELSE), Token(Token.EOL)])
        elif branch[0].value == "ELSE IF":
            if len(branch) < 3:
                return node
            header = ElseIfHeader(
                [
                    base_separator,
                    Token(Token.ELSE_IF),
                    Token(Token.SEPARATOR, separator),
                    branch[1],
                    Token(Token.EOL),
                ]
            )
            args = branch[2:]
        else:
            if len(branch) < 2:
                return node
            condition = Token(Token.ARGUMENT, f"not ({branch[0].value})") if negate else branch[0]
            header = IfHeader(
                [
                    base_separator,
                    Token(Token.IF),
                    Token(Token.SEPARATOR, separator),
                    condition,
                    Token(Token.EOL),
                ]
            )
            args = branch[1:]
        keywords = _run_keyword_if_create_keywords(args, assign, base_separator.value + indent, separator)
        if_block = If(header=header, body=keywords, orelse=prev_if)
        prev_if = if_block
    if prev_if is None:
        return node
    prev_if.end = end
    return prev_if


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


def _split_tokens_into_lines(tokens: list[Token]) -> Generator[list[Token]]:
    """Yield tokens grouped by physical line (split on EOL)."""
    line: list[Token] = []
    for token in tokens:
        line.append(token)
        if token.type == Token.EOL:
            yield line
            line = []
    if line:
        yield line


def split_comments_by_anchor(tokens: list[Token], indent: Token | None) -> tuple[list[Comment], dict[int, list[Token]]]:
    """
    Split comments into standalone comment lines and trailing comments.

    A comment that shares a physical line with data tokens (keyword name or arguments) is considered a
    *trailing* comment and is anchored to the last data token preceding it on that line. A comment that occupies
    its own line is considered *standalone*.

    Returns a tuple of ``(standalone_comments, anchor_map)`` where ``standalone_comments`` is a list of
    ``Comment`` nodes (to be emitted before the statement) and ``anchor_map`` maps ``id(data_token)`` to the list
    of trailing comment tokens that should be rendered on the same output line as that data token.
    """
    standalone: list[Comment] = []
    anchor_map: dict[int, list[Token]] = {}
    eol = Token(Token.EOL)
    for line in _split_tokens_into_lines(tokens):
        data_tokens = [
            token for token in line if token.type not in (Token.SEPARATOR, Token.EOL, Token.CONTINUATION, Token.COMMENT)
        ]
        line_comments = get_comments(line)
        if not line_comments:
            continue
        if data_tokens:
            anchor_map.setdefault(id(data_tokens[-1]), []).extend(line_comments)
        elif indent:
            standalone.extend(Comment([indent, comment, eol]) for comment in line_comments)
        else:
            standalone.extend(Comment([comment, eol]) for comment in line_comments)
    return standalone, anchor_map


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
