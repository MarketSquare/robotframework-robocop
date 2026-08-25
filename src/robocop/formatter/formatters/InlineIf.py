from __future__ import annotations

from typing import TYPE_CHECKING

from robocop.formatter.disablers import skip_section_if_disabled
from robocop.formatter.formatters import Formatter
from robocop.formatter.utils.inline_if import InlineIfConverter

if TYPE_CHECKING:
    from robot.api.parsing import Comment, If
    from robot.parsing.model.blocks import Section


class InlineIf(Formatter):
    """
    Replaces IF blocks with inline IF.

    It will only replace IF block if it can fit in one line shorter than `line_length` (default 80) parameter and return
    variables matches for all ELSE and ELSE IF branches.

    Following code:

    ```robotframework
    *** Test Cases ***
    Test
        IF    $condition1
            Keyword    argument
        END
        IF    $condition2
            ${var}  Keyword
        ELSE
            ${var}  Keyword 2
        END
        IF    $condition1
            Keyword    argument
            Keyword 2
        END
    ```

    will be formatted to:

    ```robotframework
    *** Test Cases ***
    Test
        IF    $condition1    Keyword    argument
        ${var}    IF    $condition2    Keyword    ELSE    Keyword 2
        IF    $condition1
            Keyword    argument
            Keyword 2
        END
    ```

    Too long inline IFs (over `line_length` character limit) will be replaced with normal IF block.
    You can decide to not replace IF blocks containing ELSE or ELSE IF branches by setting `skip_else` to True.

    """

    MIN_VERSION = 5

    def __init__(self, line_length: int = 80, skip_else: bool = False) -> None:
        super().__init__()
        self.line_length = line_length
        self.skip_else = skip_else

    def _converter(self) -> InlineIfConverter:
        return InlineIfConverter(
            separator=self.formatting_config.separator,
            indent=self.formatting_config.indent,
            line_length=self.line_length,
            skip_else=self.skip_else,
        )

    @skip_section_if_disabled
    def visit_Section(self, node: Section) -> Section:  # noqa: N802
        return self.generic_visit(node)

    def visit_If(self, node: If) -> If | tuple[Comment | If, ...]:  # noqa: N802
        if node.errors or getattr(node.end, "errors", None):
            return node
        if self.disablers.is_node_disabled("InlineIf", node, full_match=False):
            return node
        converter = self._converter()
        if converter.is_inline(node):
            return converter.handle_inline(node)
        self.generic_visit(node)
        if converter.no_end(node):
            return node
        indent = node.header.tokens[0]
        if not (converter.should_format(node) and converter.assignment_identical(node)):
            return node
        return converter.to_inline(node, indent.value)
