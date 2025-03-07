from __future__ import annotations

from collections import defaultdict

from robot.api.parsing import Token
from robot.parsing.model import Statement

from robocop.formatter.disablers import skip_section_if_disabled
from robocop.formatter.exceptions import InvalidParameterValueError
from robocop.formatter.formatters import Formatter
from robocop.formatter.utils import misc


class AlignVariablesSection(Formatter):
    """
    Align variables in ``*** Variables ***`` section to columns.

    Following code:

    ```robotframework
    *** Variables ***
    ${VAR}  1
    ${LONGER_NAME}  2
    &{MULTILINE}  a=b
    ...  b=c
    ```

    will be formatted to:

    ```robotframework
    *** Variables ***
    ${VAR}          1
    ${LONGER_NAME}  2
    &{MULTILINE}    a=b
    ...             b=c
    ```

    You can configure how many columns should be aligned to the longest token in given column. The remaining columns
    will use fixed length separator length ``--space-count``. By default, only first two columns are aligned.
    To align first three columns:

    ```console
    robocop format --select AlignVariablesSection.up_to_column=3
    ```

    To align all columns set ``up_to_column`` to 0.
    """

    def __init__(
        self, up_to_column: int = 2, skip_types: str = "", min_width: int | None = None, fixed_width: int | None = None
    ):
        super().__init__()
        self.up_to_column = up_to_column - 1
        self.min_width = min_width
        self.fixed_width = fixed_width
        self.skip_types = self.parse_skip_types(skip_types)

    def parse_skip_types(self, skip_types):
        allow_types = {"dict": "&", "list": "@", "scalar": "$"}
        ret = set()
        if not skip_types:
            return ret
        for skip_type in skip_types.split(","):
            if skip_type not in allow_types:
                raise InvalidParameterValueError(
                    self.__class__.__name__,
                    "skip_type",
                    skip_type,
                    "Variable types should be provided in comma separated list:\nskip_type=dict,list,scalar",
                )
            ret.add(allow_types[skip_type])
        return ret

    def should_parse(self, node):
        if not node.name:
            return True
        return node.name[0] not in self.skip_types

    @skip_section_if_disabled
    def visit_VariableSection(self, node):  # noqa: N802
        statements = []
        for child in node.body:
            if self.disablers.is_node_disabled("AlignVariablesSection", child):
                statements.append(child)
            elif child.type in (Token.EOL, Token.COMMENT):
                statements.append(misc.left_align(child))
            elif self.should_parse(child):
                statements.append(list(misc.tokens_by_lines(child)))
            else:
                statements.append(child)
        nodes_to_be_aligned = [st for st in statements if isinstance(st, list)]
        if not nodes_to_be_aligned:
            return node
        look_up = self.create_look_up(nodes_to_be_aligned)  # for every col find the longest value
        node.body = self.align_rows(statements, look_up)
        return node

    def align_rows(self, statements, look_up):
        aligned_statements = []
        for st in statements:
            if not isinstance(st, list):
                aligned_statements.append(st)
                continue
            aligned_statement = []
            for line in st:
                if misc.is_blank_multiline(line):
                    line[-1].value = line[-1].value.lstrip(" \t")  # normalize eol from '  \n' to '\n'
                    aligned_statement.extend(line)
                    continue
                up_to = self.up_to_column if self.up_to_column != -1 else len(line) - 2
                for index, token in enumerate(line[:-2]):
                    aligned_statement.append(token)
                    separator = self.get_separator(index, up_to, token, look_up)
                    aligned_statement.append(Token(Token.SEPARATOR, separator))
                last_token = line[-2]
                # remove leading whitespace before token
                last_token.value = last_token.value.strip() if last_token.value else last_token.value
                aligned_statement.append(last_token)
                aligned_statement.append(line[-1])  # eol
            aligned_statements.append(Statement.from_tokens(aligned_statement))
        return aligned_statements

    def get_separator(self, index: int, up_to: int, token, look_up: dict[int, int]) -> str:
        if index < up_to:
            if self.fixed_width:
                return max(self.fixed_width - len(token.value), self.formatting_config.space_count) * " "
            return (look_up[index] - len(token.value)) * " "
        return self.formatting_config.separator

    def create_look_up(self, statements) -> dict[int, int]:
        look_up = defaultdict(int)
        for st in statements:
            for line in st:
                up_to = self.up_to_column if self.up_to_column != -1 else len(line)
                for index, token in enumerate(line[:up_to]):
                    look_up[index] = max(look_up[index], len(token.value))
        for index, length in look_up.items():
            min_for_token = length + self.formatting_config.space_count
            if self.min_width:
                min_for_token = max(min_for_token, self.min_width)
            look_up[index] = misc.round_to_four(min_for_token)
        return look_up
