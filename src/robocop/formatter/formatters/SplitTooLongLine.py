from __future__ import annotations

from typing import TYPE_CHECKING

from robot.api.parsing import Comment, Token

try:
    from robot.api.parsing import InlineIfHeader
except ImportError:
    InlineIfHeader = None

from robocop.formatter.disablers import skip_if_disabled, skip_section_if_disabled
from robocop.formatter.formatters import Formatter
from robocop.linter.utils.disablers import DISABLER_PATTERN
from robocop.parsing.run_keywords import RUN_KEYWORDS
from robocop.version_handling import INLINE_IF_SUPPORTED

if TYPE_CHECKING:
    from collections.abc import Generator

    from robot.parsing.model.blocks import If, Section
    from robot.parsing.model.statements import (
        Arguments,
        ForceTags,
        KeywordCall,
        LibraryImport,
        Statement,
        Tags,
        Var,
        Variable,
    )


EOL = Token(Token.EOL)
CONTINUATION = Token(Token.CONTINUATION)


class SplitTooLongLine(Formatter):
    """
    Split too long lines.

    If a line exceeds the given length limit (default 120), it will be split:

    ```robotframework
    *** Keywords ***
    Keyword
        Keyword With Longer Name    ${arg1}    ${arg2}    ${arg3}  # let's assume that arg2 is at 120 char
    ```

    To:

    ```robotframework
    *** Keywords ***
    Keyword
        # let's assume that arg2 is at 120 char
        Keyword With Longer Name
        ...    ${arg1}
        ...    ${arg2}
        ...    ${arg3}
    ```

    Allowed line length is configurable using global parameter ``--line-length``:

    ```
    robocop format --line-length 140 src.robot
    ```

    Or using dedicated for this formatter parameter ``line_length``:

    ```
    robocop format --configure SplitTooLongLine.line_length:140 src.robot
    ```

    ``split_on_every_arg``, `split_on_every_value`` and ``split_on_every_setting_arg`` flags (``True`` by default)
    control whether arguments and values are split or fills the line until character limit:

    ```robotframework
    *** Test Cases ***
    Test with split_on_every_arg = True (default)
        # arguments are split
        Keyword With Longer Name
        ...    ${arg1}
        ...    ${arg2}
        ...    ${arg3}

    Test with split_on_every_arg = False
        # ${arg1} fits under limit, so it stays in the line
        Keyword With Longer Name    ${arg1}
        ...    ${arg2}    ${arg3}

    ```

    Supports global formatting params: ``space-count`` and ``separator``.
    """

    IGNORED_WHITESPACE = {Token.EOL, Token.CONTINUATION}
    HANDLES_SKIP = frozenset({"skip_comments", "skip_keyword_call", "skip_keyword_call_pattern", "skip_sections"})
    ARGUMENTS_ONLY = frozenset({Token.ARGUMENT})

    def __init__(
        self,
        line_length: int | str | None = None,
        split_on_every_arg: bool = True,
        split_on_every_value: bool = True,
        split_on_every_setting_arg: bool = True,
        split_single_value: bool = False,
        align_new_line: bool = False,
    ) -> None:
        super().__init__()
        # TODO: Replace Robot importer
        self._line_length: int | None = int(line_length) if line_length is not None else None
        self.split_on_every_arg = split_on_every_arg
        self.split_on_every_value = split_on_every_value
        self.split_on_every_setting_arg = split_on_every_setting_arg
        self.split_single_value = split_single_value
        self.align_new_line = align_new_line

    @property
    def line_length(self) -> int:
        return self.formatting_config.line_length if self._line_length is None else self._line_length

    def is_run_keyword(self, kw_name: str) -> bool:
        """
        Skip formatting if the keyword is already handled by IndentNestedKeywords formatter.

        Special indentation is preserved thanks for this.
        """
        if "IndentNestedKeywords" not in self.formatters:
            return False
        return kw_name in RUN_KEYWORDS

    @skip_section_if_disabled
    def visit_Section(self, node: Section) -> Section:  # noqa: N802
        return self.generic_visit(node)

    def visit_If(self, node: If) -> If:  # noqa: N802
        if self.is_inline(node):
            return node
        return self.generic_visit(node)

    @staticmethod
    def is_inline(node: If) -> bool:
        return INLINE_IF_SUPPORTED and isinstance(node.header, InlineIfHeader)

    def should_format_node(self, node: Statement) -> bool:
        if not self.any_line_too_long(node):
            return False
        # find if any line contains more than one data tokens - so we have something to split
        for line in node.lines:
            count = 0
            for token in line:
                if token.type not in Token.NON_DATA_TOKENS:
                    count += 1
                if count > 1:
                    return True
        return False

    def any_line_too_long(self, node: Statement) -> bool:
        for line in node.lines:
            if self.skip.comments:
                line = "".join(token.value for token in line if token.type != Token.COMMENT)
            else:
                line = "".join(token.value for token in line)
            line = DISABLER_PATTERN.sub("", line)
            line = line.rstrip().expandtabs(4)
            if len(line) >= self.line_length:
                return True
        return False

    def visit_KeywordCall(self, node: KeywordCall) -> KeywordCall:  # noqa: N802
        if self.skip.keyword_call(node):
            return node
        if not self.should_format_node(node):
            return node
        if self.disablers.is_node_disabled("SplitTooLongLine", node, full_match=False):
            return node
        if self.is_run_keyword(node.keyword):
            return node
        return self.split_keyword_call(node)

    def visit_Var(self, node: Var) -> Var | tuple[Comment, ...]:  # noqa: N802
        if self.disablers.is_node_disabled("SplitTooLongLine", node, full_match=False) or not self.should_format_node(
            node
        ):
            return node
        var_name = node.get_token(Token.VARIABLE)
        if not var_name:
            return node
        indent = node.tokens[0]
        separator = Token(Token.SEPARATOR, self.formatting_config.separator)
        line: list[Token] = [indent, node.data_tokens[0], separator, var_name]
        tokens, comments = self.split_tokens(
            node.tokens, line, self.split_on_every_value, indent=indent, split_types={Token.ARGUMENT, Token.OPTION}
        )
        node.tokens = self.insert_comments_in_first_line(tokens, comments)
        return (*comments, node)

    @staticmethod
    def insert_comments_in_first_line(tokens: list[Token], comments: list[Token]) -> list[Token]:
        if not comments:
            return tokens
        comment = Token(Token.COMMENT, "# " + " ".join([token.value.strip("# ") for token in comments]))
        eol_index = next((i for i, token in enumerate(tokens) if token.type == Token.EOL), None)
        if not eol_index:
            return tokens
        separator = Token(Token.SEPARATOR, "  ")
        return [*tokens[:eol_index], separator, comment, *tokens[eol_index:]]

    @skip_if_disabled
    def visit_Variable(self, node: Variable) -> Variable:  # noqa: N802
        if not self.should_format_node(node):
            return node
        return self.split_variable_def(node)

    @skip_if_disabled
    def visit_Tags(self, node: Tags) -> Tags | tuple[Tags, Comment]:  # noqa: N802
        if self.skip.setting("tags"):  # TODO test
            return node
        return self.split_setting_with_args(node, settings_section=False)

    @skip_if_disabled
    def visit_Arguments(self, node: Arguments) -> Arguments | tuple[Arguments, Comment]:  # noqa: N802
        if self.skip.setting("arguments"):
            return node
        return self.split_setting_with_args(node, settings_section=False)

    @skip_if_disabled
    def visit_ForceTags(self, node: ForceTags) -> ForceTags | tuple[ForceTags, Comment]:  # noqa: N802
        if self.skip.setting("tags"):
            return node
        return self.split_setting_with_args(node, settings_section=True)

    visit_DefaultTags = visit_KeywordTags = visit_TestTags = visit_ForceTags  # noqa: N815

    @skip_if_disabled
    def visit_LibraryImport(self, node: LibraryImport) -> LibraryImport | tuple[LibraryImport, Comment]:  # noqa: N802
        # if self.skip.setting("library"):  # TODO: skip library not available yet
        #     return node
        return self.split_setting_with_args(
            node, settings_section=True, split_types={Token.ARGUMENT, "AS", "WITH NAME"}, keep_types={Token.NAME}
        )

    def split_setting_with_args(
        self,
        node: Statement,
        settings_section: bool,
        split_types: set[str] = ARGUMENTS_ONLY,  # type: ignore[assignment]
        keep_types: set[str] | None = None,
    ) -> Statement | tuple[Statement, Comment]:
        if not self.should_format_node(node):
            return node
        if self.disablers.is_node_disabled("SplitTooLongLine", node, full_match=False):
            return node
        if settings_section:
            indent: Token | int = 0
            token_index = 1
        else:
            indent = node.tokens[0]
            token_index = 2
        line: list[Token] = list(node.tokens[:token_index])
        tokens, comments = self.split_tokens(
            node.tokens, line, self.split_on_every_setting_arg, indent, split_types=split_types, keep_types=keep_types
        )
        if indent:
            comments = [Comment([indent, comment, EOL]) for comment in comments]
        else:
            comments = [Comment([comment, EOL]) for comment in comments]
        node.tokens = tokens
        return (node, *comments)

    @staticmethod
    def join_on_separator(tokens: list[Token], separator: Token) -> Generator[Token, None, None]:
        for token in tokens:
            yield token
            yield separator

    @staticmethod
    def split_to_multiple_lines(tokens: list[Token], indent: Token, separator: Token) -> Generator[Token, None, None]:
        first = True
        for token in tokens:
            yield indent
            if not first:
                yield CONTINUATION
                yield separator
            yield token
            yield EOL
            first = False

    def split_tokens(
        self,
        tokens: list[Token],
        line: list[Token],
        split_on: bool,
        indent: Token | int | None = None,
        split_types: set[str] = ARGUMENTS_ONLY,  # type: ignore[assignment]
        keep_types: set[str] | None = None,
    ) -> tuple[list[Token], list[Token]]:
        if not keep_types:
            keep_types = set()
        separator = Token(Token.SEPARATOR, self.formatting_config.separator)
        align_new_line = self.align_new_line and not split_on
        if align_new_line:
            cont_indent = None
        else:
            cont_indent = Token(Token.SEPARATOR, self.formatting_config.continuation_indent)
        split_tokens: list[Token] = []
        comments: list[Token] = []
        # Comments with separators inside them are split into
        # [COMMENT, SEPARATOR, COMMENT] tokens in the AST, so to preserve the
        # original comment, we need a lookback at the separator tokens.
        last_separator = None
        for token in tokens:
            if token.type in self.IGNORED_WHITESPACE:
                continue
            if token.type == Token.SEPARATOR:
                last_separator = token
            elif token.type == Token.COMMENT:
                self.join_split_comments(comments, token, last_separator)
            elif token.type in split_types:
                if token.value == "":
                    token.value = "${EMPTY}"
                if split_on or not self.col_fit_in_line([*line, separator, token]):
                    if align_new_line and cont_indent is None:  # we are yet to calculate aligned indent
                        cont_indent = Token(Token.SEPARATOR, self.calculate_align_separator(line))
                    line.append(EOL)
                    split_tokens.extend(line)
                    if indent:
                        line = [indent, CONTINUATION, cont_indent, token]
                    else:
                        line = [CONTINUATION, cont_indent, token]
                else:
                    line.extend([separator, token])
            elif token.type in keep_types:
                line.extend([separator, token])
        split_tokens.extend(line)
        split_tokens.append(EOL)
        return split_tokens, comments

    @staticmethod
    def join_split_comments(comments: list[Token], token: Token, last_separator: Token | None) -> None:
        """
        Join split comments when splitting line.

        AST splits comments with separators, e.g.
        "# Comment     rest" -> ["# Comment", "     ", "rest"].
        Notice the third value not starting with a hash - we need to join such comment with previous comment.
        """
        if comments and not token.value.startswith("#"):
            comments[-1].value += last_separator.value + token.value  # type: ignore[union-attr]
        else:
            comments.append(token)

    def calculate_align_separator(self, line: list[Token]) -> str:
        """Calculate width of the separator required to align new line to previous line."""
        if len(line) <= 2:
            # line only fits one column, so we don't have anything to align it for
            return self.formatting_config.continuation_indent
        first_data_token = next((token.value for token in line if token.type != Token.SEPARATOR), "")
        # Decrease by 3 for ... token
        align_width = len(first_data_token) + len(self.formatting_config.separator) - 3
        return align_width * " "

    def split_variable_def(self, node: Variable) -> Variable | tuple[Comment, ...]:
        if len(node.value) < 2 and not self.split_single_value:
            return node
        line = [node.data_tokens[0]]
        tokens, comments = self.split_tokens(node.tokens, line, self.split_on_every_value)
        comments = [Comment([comment, EOL]) for comment in comments]
        node.tokens = tokens
        return (*comments, node)

    def split_keyword_call(self, node: KeywordCall) -> KeywordCall:
        separator = Token(Token.SEPARATOR, self.formatting_config.separator)
        cont_indent = Token(Token.SEPARATOR, self.formatting_config.continuation_indent)
        indent = node.tokens[0]

        keyword = node.get_token(Token.KEYWORD)
        if not keyword:
            return node
        # check if assign tokens needs to be split too
        assign = node.get_tokens(Token.ASSIGN)
        line: list[Token] = [indent, *self.join_on_separator(assign, separator), keyword]
        if assign and not self.col_fit_in_line(line):
            head: list[Token] = [
                *self.split_to_multiple_lines(assign, indent=indent, separator=cont_indent),
                indent,
                CONTINUATION,
                cont_indent,
                keyword,
            ]
            line = []
        else:
            head = []
        tokens, comments = self.split_tokens(
            node.tokens[node.tokens.index(keyword) + 1 :], line, self.split_on_every_arg, indent
        )
        head.extend(tokens)
        node.tokens = self.insert_comments_in_first_line(head, comments)
        return node

    def col_fit_in_line(self, tokens: list[Token]) -> bool:
        return self.len_token_text(tokens) < self.line_length

    @staticmethod
    def len_token_text(tokens: list[Token]) -> int:
        return sum(len(token.value) for token in tokens)
