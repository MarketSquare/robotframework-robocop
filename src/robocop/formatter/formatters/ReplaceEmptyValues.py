from __future__ import annotations

from typing import TYPE_CHECKING

from robot.api.parsing import Keyword, KeywordSection, TestCase, TestCaseSection, Token, Var

from robocop.formatter.disablers import skip_if_disabled, skip_section_if_disabled
from robocop.formatter.formatters import Formatter

if TYPE_CHECKING:
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
    - List of sections - e.g., ``["variables", "keywords"]``

    Configuration example in pyproject.toml:
    ```toml
    [tool.robocop.format]
    configure = [
        "ReplaceEmptyValues.sections=all",
        # or
        "ReplaceEmptyValues.sections=['variables','keywords']",
    ]
    ```
    """

    HANDLES_SKIP = frozenset({"skip_sections"})

    def __init__(self, sections: str | list[str] = "variables") -> None:
        super().__init__()
        if isinstance(sections, str):
            if sections == "all":
                self.enabled_sections = {"variables", "keywords", "testcases"}
            else:
                self.enabled_sections = {s.strip().lower() for s in sections.split(",")}
        else:
            self.enabled_sections = {s.lower() for s in sections}
        self.current_section: str | None = None  # Track which section we're currently visiting

    @skip_section_if_disabled
    def visit_VariableSection(self, node: VariableSection) -> VariableSection:  # noqa: N802
        if "variables" not in self.enabled_sections:
            return node
        self.current_section = "variables"
        result = self.generic_visit(node)
        self.current_section = None
        return result

    @skip_section_if_disabled
    def visit_TestCaseSection(self, node: TestCaseSection) -> TestCaseSection:  # noqa: N802
        if "testcases" not in self.enabled_sections:
            return node
        self.current_section = "testcases"
        result = self.generic_visit(node)
        self.current_section = None
        return result

    @skip_section_if_disabled
    def visit_KeywordSection(self, node: KeywordSection) -> KeywordSection:  # noqa: N802
        if "keywords" not in self.enabled_sections:
            return node
        self.current_section = "keywords"
        result = self.generic_visit(node)
        self.current_section = None
        return result

    @skip_if_disabled
    def visit_TestCase(self, node: TestCase) -> TestCase:  # noqa: N802
        return self.generic_visit(node)

    @skip_if_disabled
    def visit_Keyword(self, node: Keyword) -> Keyword:  # noqa: N802
        return self.generic_visit(node)

    @skip_if_disabled
    def visit_Variable(self, node: Variable) -> Variable:  # noqa: N802
        if self.current_section != "variables":
            return node
        if node.errors or not node.name:
            return node
        args = node.get_tokens(Token.ARGUMENT)
        sep = Token(Token.SEPARATOR, self.formatting_config.separator)
        new_line_sep = Token(Token.SEPARATOR, self.formatting_config.continuation_indent)
        if args:
            tokens = []
            prev_token = None
            for token in node.tokens:
                if token.type == Token.ARGUMENT and not token.value:
                    if not prev_token or prev_token.type != Token.SEPARATOR:
                        tokens.append(new_line_sep)
                    tokens.append(Token(Token.ARGUMENT, "${EMPTY}"))
                else:
                    if token.type == Token.EOL:
                        token.value = token.value.lstrip(" ")
                    tokens.append(token)
                prev_token = token
        else:
            tokens = [node.tokens[0], sep, Token(Token.ARGUMENT, node.name[0] + "{EMPTY}"), *node.tokens[1:]]
        node.tokens = tokens
        return node

    @skip_if_disabled
    def visit_Var(self, node: Var) -> Var:  # noqa: N802
        """Handle inline VAR statements to replace empty values with proper EMPTY variables."""
        if self.current_section not in ("testcases", "keywords"):
            return node
        if Var is None or node.errors:
            return node

        variable_token = node.get_token(Token.VARIABLE)
        if not variable_token:
            return node

        args = node.get_tokens(Token.ARGUMENT)
        if args:
            return node

        var_name = variable_token.value
        if var_name.startswith("${"):
            empty_value = "${EMPTY}"
        elif var_name.startswith("@{"):
            empty_value = "@{EMPTY}"
        elif var_name.startswith("&{"):
            empty_value = "&{EMPTY}"
        else:
            return node

        sep = Token(Token.SEPARATOR, self.formatting_config.separator)
        tokens = []
        for token in node.tokens:
            tokens.append(token)
            if token == variable_token:
                tokens.append(sep)
                tokens.append(Token(Token.ARGUMENT, empty_value))

        node.tokens = tokens
        return node
