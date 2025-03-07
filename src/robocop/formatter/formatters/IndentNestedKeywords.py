from robot.api.parsing import Token

from robocop.formatter.disablers import skip_if_disabled
from robocop.formatter.exceptions import InvalidParameterValueError
from robocop.formatter.formatters import Formatter
from robocop.formatter.formatters.run_keywords import get_run_keywords
from robocop.formatter.skip import Skip
from robocop.formatter.utils import misc


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

    To skip formatting run keywords inside settings (such as ``Suite Setup``, ``[Setup]``, ``[Teardown]`` etc.) set
    ``skip_settings`` to ``True``.
    """

    ENABLED = False
    HANDLES_SKIP = frozenset({"skip_settings"})

    def __init__(self, indent_and: str = "split", skip: Skip = None):
        super().__init__(skip=skip)
        self.indent_and = indent_and
        self.validate_indent_and()
        self.run_keywords = get_run_keywords()

    def validate_indent_and(self):
        modes = {"keep_in_line", "split", "split_and_indent"}
        if self.indent_and not in modes:
            raise InvalidParameterValueError(
                self.__class__.__name__,
                "indent_and",
                self.indent_and,
                f"Select one of: {','.join(modes)}",
            )

    def get_run_keyword(self, kw_name):
        kw_norm = misc.normalize_name(kw_name)
        return self.run_keywords.get(kw_norm, None)

    def get_setting_lines(self, node, indent):
        if self.skip.setting("any") or node.errors or not len(node.data_tokens) > 1:
            return None
        run_keyword = self.get_run_keyword(node.data_tokens[1].value)
        if not run_keyword:
            return None
        lines = self.parse_sub_kw(node.data_tokens[1:])
        if not lines:
            return None
        return self.split_too_long_lines(lines, indent)

    def get_separator(self, column=1, continuation=False):
        if continuation:
            separator = self.formatting_config.continuation_indent * column
        else:
            separator = self.formatting_config.separator * column
        return Token(Token.SEPARATOR, separator)

    def parse_keyword_lines(self, lines, tokens, new_line, eol):
        separator = self.get_separator()
        for column, line in lines[1:]:
            tokens.extend(new_line)
            tokens.append(self.get_separator(column, continuation=True))
            tokens.extend(misc.join_tokens_with_token(line, separator))
        tokens.append(eol)
        return tokens

    @staticmethod
    def node_was_formatted(old_tokens, new_tokens) -> bool:
        """Compare code before and after formatting while ignoring comments to check if code was formatted."""
        if len(new_tokens) > len(old_tokens):
            return True
        old_tokens_no_comm = []
        data_in_line = False
        for token in old_tokens:
            if token.type == Token.EOL:
                if not data_in_line:
                    continue
                data_in_line = False
            elif token.type == Token.COMMENT:
                if old_tokens_no_comm and old_tokens_no_comm[-1].type == Token.SEPARATOR:
                    old_tokens_no_comm.pop()
                continue
            elif token.type != Token.SEPARATOR:
                data_in_line = True
            old_tokens_no_comm.append(token)
        if len(new_tokens) != len(old_tokens_no_comm):
            return True
        for new_token, old_token in zip(new_tokens, old_tokens_no_comm):
            if new_token.type != old_token.type or new_token.value != old_token.value:
                return True
        return False

    @skip_if_disabled
    def visit_SuiteSetup(self, node):  # noqa: N802
        lines = self.get_setting_lines(node, 0)
        if not lines:
            return node
        comments = misc.collect_comments_from_tokens(node.tokens, indent=None)
        separator = self.get_separator()
        new_line = misc.get_new_line()
        tokens = [node.data_tokens[0], separator, *misc.join_tokens_with_token(lines[0][1], separator)]
        formatted_tokens = self.parse_keyword_lines(lines, tokens, new_line, eol=node.tokens[-1])
        if self.node_was_formatted(node.tokens, formatted_tokens):
            node.tokens = formatted_tokens
            return (*comments, node)
        return node

    visit_SuiteTeardown = visit_TestSetup = visit_TestTeardown = visit_SuiteSetup  # noqa: N815

    @skip_if_disabled
    def visit_Setup(self, node):  # noqa: N802
        indent = len(node.tokens[0].value)
        lines = self.get_setting_lines(node, indent)
        if not lines:
            return node
        indent = node.tokens[0]
        separator = self.get_separator()
        new_line = misc.get_new_line(indent)
        tokens = [indent, node.data_tokens[0], separator, *misc.join_tokens_with_token(lines[0][1], separator)]
        comment = misc.merge_comments_into_one(node.tokens)
        if comment:
            # need to add comments on first line for [Setup] / [Teardown] settings
            comment_sep = Token(Token.SEPARATOR, "  ")
            tokens.extend([comment_sep, comment])
        node.tokens = self.parse_keyword_lines(lines, tokens, new_line, eol=node.tokens[-1])
        return node

    visit_Teardown = visit_Setup  # noqa: N815

    @skip_if_disabled
    def visit_KeywordCall(self, node):  # noqa: N802
        if node.errors or not node.keyword:
            return node
        run_keyword = self.get_run_keyword(node.keyword)
        if not run_keyword:
            return node

        indent = node.tokens[0]
        comments = misc.collect_comments_from_tokens(node.tokens, indent)
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
        formatted_tokens = self.parse_keyword_lines(lines, tokens, new_line, eol=node.tokens[-1])
        if self.node_was_formatted(node.tokens, formatted_tokens):
            node.tokens = formatted_tokens
            return (*comments, node)
        return node

    def split_too_long_lines(self, lines, indent):
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

    def calculate_line_indent(self, column, starting_indent):
        """
        Calculate with of the continuation indent.

        For example following line will have 4 + 3 + 2x column x 4 indent with:

            ...        argument
        """
        return starting_indent + len(self.formatting_config.continuation_indent) * column + 3

    def parse_sub_kw(self, tokens, column=0):
        if not tokens:
            return []
        run_keyword = self.get_run_keyword(tokens[0].value)
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

    def split_on_else(self, tokens, lines, column):
        column = max(column, 1)
        prefix, branch, tokens = misc.split_on_token_value(tokens, "ELSE", 1)
        lines.extend(self.parse_sub_kw(prefix, column + 1))
        lines.append((column, branch))
        lines.extend(self.parse_sub_kw(tokens, column + 1))
        return lines

    def split_on_and(self, tokens, lines, column):
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
