from robot.api.parsing import Token
from robotidy.disablers import skip_if_disabled, skip_section_if_disabled
from robotidy.skip import Skip
from robotidy.transformers import Transformer


class ReplaceEmptyValues(Transformer):
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

    To be more explicit, this transformer replace such values with ``${EMPTY}`` variables:

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
    """

    HANDLES_SKIP = frozenset({"skip_sections"})

    def __init__(self, skip: Skip = None):
        super().__init__(skip)

    @skip_section_if_disabled
    def visit_VariableSection(self, node):  # noqa
        return self.generic_visit(node)

    @skip_if_disabled
    def visit_Variable(self, node):  # noqa
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
