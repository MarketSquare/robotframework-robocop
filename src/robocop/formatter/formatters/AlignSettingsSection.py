from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from robot.api.parsing import Documentation, Token
from robot.parsing.model import Statement

from robocop.formatter.disablers import skip_section_if_disabled
from robocop.formatter.formatters import Formatter
from robocop.formatter.utils import misc

if TYPE_CHECKING:
    from robocop.formatter.skip import Skip


class AlignSettingsSection(Formatter):
    """
    Align statements in ``*** Settings ***`` section to columns.

    Following code:

    ```robotframework
    *** Settings ***
    Library      SeleniumLibrary
    Library   Mylibrary.py
    Variables  variables.py
    Test Timeout  1 min
        # this should be left aligned
    ```

    will be formatted to:

    ```robotframework
    *** Settings ***
    Library         SeleniumLibrary
    Library         Mylibrary.py
    Variables       variables.py
    Test Timeout    1 min
    # this should be left aligned
    ```

    You can configure how many columns should be aligned to the longest token in given column. The remaining columns
    will use fixed length separator length ``--space-count``. By default, only first two columns are aligned.
    To align first three columns:

    ```
    robocop format --select AlignSettingsSection.up_to_column=3
    ```

    To align all columns set ``up_to_column`` to 0.

    Arguments inside keywords in Suite Setup, Suite Teardown, Test Setup and Test Teardown are indented by additional
    ``argument_indent`` (default ``4``) spaces:

    ```robotframework
    *** Settings ***
    Suite Setup         Start Session
    ...                     host=${IPADDRESS}
    ...                     user=${USERNAME}
    ...                     password=${PASSWORD}
    Suite Teardown      Close Session
    ```

    To disable it configure ``argument_indent`` with ``0``.

    Supports global formatting param ``--space-count`` (for columns with fixed length).
    """

    TOKENS_WITH_ARGUMENTS = {
        Token.SUITE_SETUP,
        Token.SUITE_TEARDOWN,
        Token.TEST_SETUP,
        Token.TEST_TEARDOWN,
        Token.LIBRARY,
        Token.VARIABLES,
    }
    HANDLES_SKIP = frozenset({"skip_documentation"})

    def __init__(
        self,
        up_to_column: int = 2,
        argument_indent: int = 4,
        min_width: int | None = None,
        fixed_width: int | None = None,
        skip: Skip | None = None,
    ):
        super().__init__(skip=skip)
        self.up_to_column = up_to_column - 1
        self.argument_indent = argument_indent
        self.min_width = min_width
        self.fixed_width = fixed_width

    @skip_section_if_disabled
    def visit_SettingSection(self, node):  # noqa: N802
        statements = []
        for child in node.body:
            if self.disablers.is_node_disabled("AlignSettingsSection", child) or self.is_node_skip(child):
                statements.append(child)
            elif child.type in (Token.EOL, Token.COMMENT):
                statements.append(misc.left_align(child))
            else:
                statements.append(list(misc.tokens_by_lines(child)))
        nodes_to_be_aligned = [st for st in statements if isinstance(st, list)]
        if not nodes_to_be_aligned:
            return node
        look_up = self.create_look_up(nodes_to_be_aligned)  # for every col find longest value
        node.body = self.align_rows(statements, look_up)
        return node

    def is_node_skip(self, node) -> bool:
        return isinstance(node, Documentation) and self.skip.documentation

    def should_indent_arguments(self, statement):
        statement_type = statement[0][0].type
        is_library = statement_type == Token.LIBRARY
        if is_library:
            return is_library, True
        return is_library, statement_type in self.TOKENS_WITH_ARGUMENTS

    def align_rows(self, statements, look_up):
        aligned_statements = []
        for st in statements:
            if not isinstance(st, list):
                aligned_statements.append(st)
                continue
            is_library, indent_args = self.should_indent_arguments(st)
            aligned_statement = []
            for line in st:
                if misc.is_blank_multiline(line):
                    line[-1].value = line[-1].value.lstrip(" \t")  # normalize eol from '  \n' to '\n'
                    aligned_statement.extend(line)
                    continue
                indent_arg = indent_args and line[0].type == Token.CONTINUATION
                if indent_arg and is_library:
                    indent_arg = all(token.type != Token.WITH_NAME for token in line)
                up_to = self.up_to_column if self.up_to_column != -1 else len(line) - 2
                for index, token in enumerate(line[:-2]):
                    aligned_statement.append(token)
                    separator = self.calc_separator(index, up_to, indent_arg, token, look_up)
                    aligned_statement.append(Token(Token.SEPARATOR, separator))
                last_token = line[-2]
                # remove leading whitespace before token
                last_token.value = last_token.value.strip() if last_token.value else last_token.value
                aligned_statement.append(last_token)
                aligned_statement.append(line[-1])  # eol
            aligned_statements.append(Statement.from_tokens(aligned_statement))
        return aligned_statements

    def calc_separator(self, index, up_to, indent_arg, token, look_up):
        if index < up_to:
            if self.fixed_width:
                return max(self.fixed_width - len(token.value), self.formatting_config.space_count) * " "
            arg_indent = self.argument_indent if indent_arg else 0
            if indent_arg and index != 0:
                return (
                    max(
                        (look_up[index] - len(token.value) - arg_indent + 4),
                        self.formatting_config.space_count,
                    )
                    * " "
                )
            return (look_up[index] - len(token.value) + arg_indent + 4) * " "
        return self.formatting_config.space_count * " "

    def create_look_up(self, statements):
        look_up = defaultdict(int)
        for st in statements:
            is_doc = st[0][0].type == Token.DOCUMENTATION
            for line in st:
                if is_doc:
                    up_to = 1
                elif self.up_to_column != -1:
                    up_to = self.up_to_column
                else:
                    up_to = len(line)
                for index, token in enumerate(line[:up_to]):
                    look_up[index] = max(look_up[index], len(token.value))
        if self.min_width:
            look_up = {index: max(length, self.min_width - 4) for index, length in look_up.items()}
        return {index: misc.round_to_four(length) for index, length in look_up.items()}
