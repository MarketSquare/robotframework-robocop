from __future__ import annotations

from typing import TYPE_CHECKING

from robot.api.parsing import Keyword, KeywordSection, TestCase, TestCaseSection, Token

try:  # RF7+
    from robot.api.parsing import Var
except ImportError:
    Var = None

from robocop.formatter.disablers import skip_if_disabled, skip_section_if_disabled
from robocop.formatter.formatters import Formatter

if TYPE_CHECKING:
    from collections.abc import Sequence

    from robot.parsing.model.blocks import VariableSection
    from robot.parsing.model.statements import Variable


class ReplaceEmptyValues(Formatter):
    """
    Replace empty values with ``${EMPTY}`` variable.

    Empty variables, lists or elements in the list can be defined in the following way:

    ```robotframework
    *** Variables ***
    ${EMPTY_VALUE}
    @{EMPTY_LIST}
    &{EMPTY_DICT}
    @{LIST_WITH_EMPTY}
    ...    value
    ...
    ...    value3
    ```

    To be more explicit, this formatter replace such values with ``${EMPTY}`` variables:

    ```robotframework
    *** Variables ***
    ${EMPTY_VALUE}    ${EMPTY}
    @{EMPTY_LIST}     @{EMPTY}
    &{EMPTY_DICT}     &{EMPTY}
    @{LIST_WITH_EMPTY}
    ...    value
    ...    ${EMPTY}
    ...    value3
    ```

    By default, this formatter only processes the Variables section. You can configure
    which sections to process using the ``sections`` parameter:
    - ``variables`` (default) - only Variables section
    - ``keywords`` - only Keywords section
    - ``testcases`` - only Test Cases section
    - ``all`` - all sections
    - Comma-separated list - e.g., ``variables,keywords``

    Configuration example in pyproject.toml:
    ```toml
    [tool.robocop.format]
    configure = [
        "ReplaceEmptyValues.sections=all",
        # or
        "ReplaceEmptyValues.sections=variables,keywords",
    ]
    ```
    """

    HANDLES_SKIP = frozenset({"skip_sections"})

    def _replace_empty_args(
        self, tokens: Sequence[Token], empty_value: str, *, trim_eol: bool = False
    ) -> tuple[Token, ...]:
        """Replace empty argument tokens while preserving continuation alignment."""
        new_tokens = []
        continuation_sep = Token(Token.SEPARATOR, self.formatting_config.continuation_indent)
        prev_token = None
        for token in tokens:
            token_value = token.value or ""
            if token.type == Token.ARGUMENT and not token_value.strip():
                if not prev_token or prev_token.type != Token.SEPARATOR:
                    new_tokens.append(continuation_sep)
                new_tokens.append(Token(Token.ARGUMENT, empty_value))
            else:
                if trim_eol and token.type == Token.EOL and token.value:
                    token.value = token.value.lstrip(" ")
                new_tokens.append(token)
            prev_token = token
        return tuple(new_tokens)

    def _insert_arg_after_token(self, tokens: Sequence[Token], anchor: Token, value: str) -> tuple[Token, ...]:
        separator = Token(Token.SEPARATOR, self.formatting_config.separator)
        new_tokens = []
        for token in tokens:
            new_tokens.append(token)
            if token == anchor:
                new_tokens.append(separator)
                new_tokens.append(Token(Token.ARGUMENT, value))
        return tuple(new_tokens)

    @staticmethod
    def _get_empty_value(var_name: str) -> str | None:
        if var_name.startswith("${"):
            return "${EMPTY}"
        if var_name.startswith("@{"):
            return "@{EMPTY}"
        if var_name.startswith("&{"):
            return "&{EMPTY}"
        return None

    def __init__(self, sections: str = "variables") -> None:
        super().__init__()
        if sections == "all":
            self.enabled_sections = {"variables", "keywords", "testcases"}
        else:
            self.enabled_sections = {s.strip().lower() for s in sections.split(",")}

    @skip_section_if_disabled
    def visit_VariableSection(self, node: VariableSection) -> VariableSection:  # noqa: N802
        if "variables" not in self.enabled_sections:
            return node
        return self.generic_visit(node)

    @skip_section_if_disabled
    def visit_TestCaseSection(self, node: TestCaseSection) -> TestCaseSection:  # noqa: N802
        if "testcases" not in self.enabled_sections:
            return node
        return self.generic_visit(node)

    @skip_section_if_disabled
    def visit_KeywordSection(self, node: KeywordSection) -> KeywordSection:  # noqa: N802
        if "keywords" not in self.enabled_sections:
            return node
        return self.generic_visit(node)

    @skip_if_disabled
    def visit_TestCase(self, node: TestCase) -> TestCase:  # noqa: N802
        return self.generic_visit(node)

    @skip_if_disabled
    def visit_Keyword(self, node: Keyword) -> Keyword:  # noqa: N802
        return self.generic_visit(node)

    @skip_if_disabled
    def visit_Variable(self, node: Variable) -> Variable:  # noqa: N802
        if node.errors or not node.name:
            return node
        args = node.get_tokens(Token.ARGUMENT)
        if args:
            node.tokens = self._replace_empty_args(node.tokens, "${EMPTY}", trim_eol=True)
        else:
            node.tokens = self._insert_arg_after_token(node.tokens, node.tokens[0], node.name[0] + "{EMPTY}")
        return node

    @skip_if_disabled
    def visit_Var(self, node: Var) -> Var:  # noqa: N802
        """Handle inline VAR statements to replace empty values with proper EMPTY variables."""
        if Var is None or node.errors:
            return node

        variable_token = node.get_token(Token.VARIABLE)
        if not variable_token:
            return node

        args = node.get_tokens(Token.ARGUMENT)
        if any((arg.value or "").strip() for arg in args):
            return node

        empty_value = self._get_empty_value(variable_token.value)
        if empty_value is None:
            return node

        if args:
            node.tokens = self._replace_empty_args(node.tokens, empty_value)
        else:
            node.tokens = self._insert_arg_after_token(node.tokens, variable_token, empty_value)
        return node
