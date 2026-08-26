from __future__ import annotations

from typing import TYPE_CHECKING, Any

from robot.api.parsing import Token

from robocop.exceptions import InvalidParameterValueError
from robocop.formatter.disablers import skip_if_disabled
from robocop.formatter.formatters import Formatter
from robocop.formatter.utils import misc
from robocop.parsing.run_keywords import RUN_KEYWORDS

if TYPE_CHECKING:
    from robot.parsing.model.statements import KeywordCall, Setup, SuiteSetup


class IndentNestedKeywords(Formatter):
    """
    Format indentation inside run keywords variants such as ``Run Keywords`` or ``Run Keyword And Continue On Failure``.

    Keywords inside run keywords variants are detected and
    whitespace is formatted to outline them. This code:

    ```robotframework
        Run Keyword    Run Keyword If    ${True}    Run keywords   Log    foo    AND    Log    bar    ELSE    Log    baz
    ```

    will be formatted to:

    ```robotframework
        Run Keyword
        ...    Run Keyword If    ${True}
        ...        Run keywords
        ...            Log    foo
        ...            AND
        ...            Log    bar
        ...    ELSE
        ...        Log    baz
    ```

    ``AND`` argument inside ``Run Keywords`` can be handled in different ways. It is controlled via ``indent_and``
    parameter. For more details see the full documentation.

    Comments are kept together with the code they reference: a comment trailing data on a line stays on the same
    output line as the closest keyword or argument (rather than being moved in front of the whole statement), while a
    comment occupying its own line is kept as a standalone comment line before the statement.

    To skip formatting run keywords inside settings (such as ``Suite Setup``, ``[Setup]``, ``[Teardown]`` etc.) set
    ``skip_settings`` to ``True``.
    """

    ENABLED = False
    HANDLES_SKIP = frozenset({"skip_settings"})

    def __init__(self, indent_and: str = "split") -> None:
        super().__init__()
        self.indent_and = indent_and
        self.validate_indent_and()

    def validate_indent_and(self) -> None:
        modes = {"keep_in_line", "split", "split_and_indent"}
        if self.indent_and not in modes:
            raise InvalidParameterValueError(
                self.__class__.__name__,
                "indent_and",
                self.indent_and,
                f"Select one of: {','.join(modes)}",
            )

    def get_setting_lines(self, node: SuiteSetup | Setup, indent: int) -> list[tuple[int, list[Token]]] | None:
        if self.skip.setting("any") or node.errors or not len(node.data_tokens) > 1:
            return None
        run_keyword = RUN_KEYWORDS.get(node.data_tokens[1].value)
        if not run_keyword:
            return None
        lines = self.parse_sub_kw(node.data_tokens[1:])
        if not lines:
            return None
        return self.split_too_long_lines(lines, indent)

    def get_separator(self, column: int = 1, continuation: bool = False) -> Token:
        if continuation:
            separator = self.formatting_config.continuation_indent * column
        else:
            separator = self.formatting_config.separator * column
        return Token(Token.SEPARATOR, separator)

    def append_trailing_comments(
        self, tokens: list[Token], line: list[Token], anchor_map: dict[int, list[Token]]
    ) -> None:
        """Append comments anchored to any data token in ``line`` at the end of the current output line."""
        if not anchor_map:
            return
        for data_token in line:
            for comment in anchor_map.get(id(data_token), []):
                tokens.append(self.get_separator())
                tokens.append(comment)

    def parse_keyword_lines(
        self,
        lines: list[tuple[int, list[Token]]],
        tokens: list[Token],
        new_line: list[Token],
        eol: Token,
        anchor_map: dict[int, list[Token]] | None = None,
    ) -> list[Token]:
        anchor_map = anchor_map or {}
        separator = self.get_separator()
        self.append_trailing_comments(tokens, lines[0][1], anchor_map)
        for column, line in lines[1:]:
            tokens.extend(new_line)
            tokens.append(self.get_separator(column, continuation=True))
            tokens.extend(misc.join_tokens_with_token(line, separator))
            self.append_trailing_comments(tokens, line, anchor_map)
        tokens.append(eol)
        return tokens

    @staticmethod
    def tokens_without_comments(tokens: list[Token]) -> list[Token]:
        """Return tokens with comments (and resulting comment-only lines) removed."""
        result: list[Token] = []
        data_in_line = False
        for token in tokens:
            if token.type == Token.EOL:
                if not data_in_line:
                    continue
                data_in_line = False
            elif token.type == Token.COMMENT:
                if result and result[-1].type == Token.SEPARATOR:
                    result.pop()
                continue
            elif token.type != Token.SEPARATOR:
                data_in_line = True
            result.append(token)
        return result

    @classmethod
    def node_was_formatted(cls, old_tokens: list[Token], new_tokens: list[Token]) -> bool:
        """Compare code before and after formatting while ignoring comments to check if code was formatted."""
        old_tokens_no_comm = cls.tokens_without_comments(old_tokens)
        new_tokens_no_comm = cls.tokens_without_comments(new_tokens)
        if len(new_tokens_no_comm) != len(old_tokens_no_comm):
            return True
        for new_token, old_token in zip(new_tokens_no_comm, old_tokens_no_comm, strict=False):
            if new_token.type != old_token.type or new_token.value != old_token.value:
                return True
        return False

    @skip_if_disabled
    def visit_SuiteSetup(self, node: SuiteSetup) -> SuiteSetup | tuple[Any, ...]:  # noqa: N802
        lines = self.get_setting_lines(node, 0)
        if not lines:
            return node
        comments, anchor_map = misc.split_comments_by_anchor(node.tokens, indent=None)
        separator = self.get_separator()
        new_line = misc.get_new_line()
        tokens = [node.data_tokens[0], separator, *misc.join_tokens_with_token(lines[0][1], separator)]
        formatted_tokens = self.parse_keyword_lines(lines, tokens, new_line, eol=node.tokens[-1], anchor_map=anchor_map)
        if self.node_was_formatted(node.tokens, formatted_tokens):
            node.tokens = formatted_tokens
            return (*comments, node)
        return node

    visit_SuiteTeardown = visit_TestSetup = visit_TestTeardown = visit_SuiteSetup  # noqa: N815

    @skip_if_disabled
    def visit_Setup(self, node: Setup) -> Setup | tuple[Any, ...]:  # noqa: N802
        indent = len(node.tokens[0].value)
        lines = self.get_setting_lines(node, indent)
        if not lines:
            return node
        indent = node.tokens[0]
        separator = self.get_separator()
        new_line = misc.get_new_line(indent)
        tokens = [indent, node.data_tokens[0], separator, *misc.join_tokens_with_token(lines[0][1], separator)]
        comments, anchor_map = misc.split_comments_by_anchor(node.tokens, indent=indent)
        node.tokens = self.parse_keyword_lines(lines, tokens, new_line, eol=node.tokens[-1], anchor_map=anchor_map)
        if comments:
            return (*comments, node)
        return node

    visit_Teardown = visit_Setup  # noqa: N815

    @skip_if_disabled
    def visit_KeywordCall(self, node: KeywordCall) -> KeywordCall | tuple[Any, ...]:  # noqa: N802
        if node.errors or not node.keyword:
            return node
        run_keyword = RUN_KEYWORDS.get(node.keyword)
        if not run_keyword:
            return node

        indent = node.tokens[0]
        comments, anchor_map = misc.split_comments_by_anchor(node.tokens, indent)
        assign, kw_tokens = misc.split_on_token_type(node.data_tokens, Token.KEYWORD)
        lines = self.parse_sub_kw(kw_tokens)
        if not lines:
            return node
        lines = self.split_too_long_lines(lines, len(self.formatting_config.separator))

        separator = self.get_separator()
        tokens = [indent]
        if assign:
            tokens.extend([*misc.join_tokens_with_token(assign, separator), separator])
        tokens.extend(misc.join_tokens_with_token(lines[0][1], separator))
        new_line = misc.get_new_line(indent)
        formatted_tokens = self.parse_keyword_lines(lines, tokens, new_line, eol=node.tokens[-1], anchor_map=anchor_map)
        if self.node_was_formatted(node.tokens, formatted_tokens):
            node.tokens = formatted_tokens
            return (*comments, node)
        return node

    def split_too_long_lines(self, lines: list[tuple[int, list[Token]]], indent: int) -> list[tuple[int, list[Token]]]:
        """Parse indented lines to split too long lines"""
        # TODO: Keep things like ELSE IF <condition>, Run Keyword If <> together no matter what
        if "SplitTooLongLine" not in self.formatters:
            return lines
        allowed_length = self.formatters["SplitTooLongLine"].line_length
        sep_len = len(self.formatting_config.separator)
        new_lines = []
        for column, line in lines:
            pre_indent = self.calculate_line_indent(column, indent)
            if (
                column == 0
                or len(line) == 1
                or (pre_indent + misc.get_line_length_with_sep(line, sep_len)) <= allowed_length
            ):
                new_lines.append((column, line))
                continue
            if (pre_indent + misc.get_line_length_with_sep(line[:2], sep_len)) <= allowed_length:
                first_line_end = 2
            else:
                first_line_end = 1
            new_lines.append((column, line[:first_line_end]))
            new_lines.extend([(column + 1, [arg]) for arg in line[first_line_end:]])
        return new_lines

    def calculate_line_indent(self, column: int, starting_indent: int) -> int:
        """
        Calculate with of the continuation indent.

        For example the following line will have 4 + 3 + 2x column x 4 indent with:

            ...        argument
        """
        return starting_indent + len(self.formatting_config.continuation_indent) * column + 3

    def parse_sub_kw(self, tokens: list[Token], column: int = 0) -> list[tuple[int, list[Token]]]:
        if not tokens:
            return []
        run_keyword = RUN_KEYWORDS.get(tokens[0].value)
        if not run_keyword:
            return [(column, list(tokens))]
        lines = [(column, tokens[: run_keyword.resolve])]
        tokens = tokens[run_keyword.resolve :]
        if run_keyword.branches:
            if "ELSE IF" in run_keyword.branches:
                while misc.is_token_value_in_tokens("ELSE IF", tokens):
                    column = max(column, 1)
                    prefix, branch, tokens = misc.split_on_token_value(tokens, "ELSE IF", 2)
                    lines.extend(self.parse_sub_kw(prefix, column + 1))
                    lines.append((column, branch))
            if "ELSE" in run_keyword.branches and misc.is_token_value_in_tokens("ELSE", tokens):
                return self.split_on_else(tokens, lines, column)
        elif run_keyword.split_on_and:
            return self.split_on_and(tokens, lines, column)
        return lines + self.parse_sub_kw(tokens, column + 1)

    def split_on_else(
        self, tokens: list[Token], lines: list[tuple[int, list[Token]]], column: int
    ) -> list[tuple[int, list[Token]]]:
        column = max(column, 1)
        prefix, branch, tokens = misc.split_on_token_value(tokens, "ELSE", 1)
        lines.extend(self.parse_sub_kw(prefix, column + 1))
        lines.append((column, branch))
        lines.extend(self.parse_sub_kw(tokens, column + 1))
        return lines

    def split_on_and(
        self, tokens: list[Token], lines: list[tuple[int, list[Token]]], column: int
    ) -> list[tuple[int, list[Token]]]:
        if misc.is_token_value_in_tokens("AND", tokens):
            while misc.is_token_value_in_tokens("AND", tokens):
                prefix, branch, tokens = misc.split_on_token_value(tokens, "AND", 1)
                if self.indent_and == "keep_in_line":
                    lines.extend(self.parse_sub_kw(prefix + branch, column + 1))
                else:
                    indent = int(self.indent_and == "split_and_indent")  # indent = 1 for split_and_indent, else 0
                    lines.extend(self.parse_sub_kw(prefix, column + 1 + indent))
                    lines.append((column + 1, branch))
            indent = int(self.indent_and == "split_and_indent")  # indent = 1 for split_and_indent, else 0
            lines.extend(self.parse_sub_kw(tokens, column + 1 + indent))
        else:
            lines.extend([(column + 1, [kw_token]) for kw_token in tokens])
        return lines
