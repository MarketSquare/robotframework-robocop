from collections.abc import Iterable

from robot.api.parsing import Token

try:
    from robot.api.parsing import Break, Continue
except ImportError:
    Continue, Break = None, None

from robocop.formatter.disablers import skip_if_disabled, skip_section_if_disabled
from robocop.formatter.formatters import Formatter
from robocop.formatter.utils import misc


class ReplaceBreakContinue(Formatter):
    """
    Replace Continue For Loop and Exit For Loop keyword variants with CONTINUE and BREAK statements.

    Following code:

    ```robotframework
    *** Keywords ***
    Keyword
        FOR    ${var}    IN  1  2
            Continue For Loop
            Continue For Loop If    $condition
            Exit For Loop
            Exit For Loop If    $condition
        END
    ```

    will be formatted to:

    ```robotframework
    *** Keywords ***
    Keyword
        FOR    ${var}    IN  1  2
            CONTINUE
            IF    $condition
                CONTINUE
            END
            BREAK
            IF    $condition
                BREAK
            END
        END
    ```
    """

    MIN_VERSION = 5

    def __init__(self):
        super().__init__()
        self.in_loop = False

    def visit_File(self, node):  # noqa: N802
        self.in_loop = False
        return self.generic_visit(node)

    @skip_section_if_disabled
    def visit_Section(self, node):  # noqa: N802
        return self.generic_visit(node)

    @staticmethod
    def create_statement_from_tokens(statement, tokens: Iterable, indent: Token):
        return statement([indent, Token(statement.type), *tokens])

    @skip_if_disabled
    def visit_KeywordCall(self, node):  # noqa: N802,PLR0911
        if not self.in_loop or not node.keyword or node.errors:
            return node
        normalized_name = misc.after_last_dot(misc.normalize_name(node.keyword))
        if "forloop" not in normalized_name:
            return node
        if normalized_name == "continueforloop":
            return self.create_statement_from_tokens(statement=Continue, tokens=node.tokens[2:], indent=node.tokens[0])
        if normalized_name == "exitforloop":
            return self.create_statement_from_tokens(statement=Break, tokens=node.tokens[2:], indent=node.tokens[0])
        if normalized_name == "continueforloopif":
            return misc.wrap_in_if_and_replace_statement(node, Continue, self.formatting_config.separator)
        if normalized_name == "exitforloopif":
            return misc.wrap_in_if_and_replace_statement(node, Break, self.formatting_config.separator)
        return node

    def visit_For(self, node):  # noqa: N802
        self.in_loop = True
        node = self.generic_visit(node)
        self.in_loop = False
        return node

    visit_While = visit_For  # noqa: N815
