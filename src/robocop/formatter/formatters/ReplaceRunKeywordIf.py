from __future__ import annotations

from typing import TYPE_CHECKING

from robocop.formatter.disablers import skip_if_disabled, skip_section_if_disabled
from robocop.formatter.formatters import Formatter
from robocop.formatter.utils import misc

if TYPE_CHECKING:
    from robot.api.parsing import If, KeywordCall
    from robot.parsing.model.blocks import Section


class ReplaceRunKeywordIf(Formatter):
    """
    Replace ``Run Keyword If`` keyword calls with IF expressions.

    Following code:

    ```robotframework
    *** Keywords ***
    Keyword
        Run Keyword If  ${condition}
        ...  Keyword  ${arg}
        ...  ELSE IF  ${condition2}  Keyword2
        ...  ELSE  Keyword3
    ```

    Will be formatted to:

    ```robotframework
    *** Keywords ***
    Keyword
        IF    ${condition}
            Keyword    ${arg}
        ELSE IF    ${condition2}
            Keyword2
        ELSE
            Keyword3
        END
    ```

    Any return value will be applied to every ``ELSE``/``ELSE IF`` branch:

    ```robotframework
    *** Keywords ***
    Keyword
        ${var}  Run Keyword If  ${condition}  Keyword  ELSE  Keyword2
    ```

    Output:

    ```robotframework
    *** Keywords ***
    Keyword
        IF    ${condition}
            ${var}    Keyword
        ELSE
            ${var}    Keyword2
        END
    ```

    Run Keywords inside Run Keyword If will be split into separate keywords:

    ```robotframework
    *** Keywords ***
    Keyword
        Run Keyword If  ${condition}  Run Keywords  Keyword  ${arg}  AND  Keyword2
    ```

    Output:

    ```robotframework
    *** Keywords ***
    Keyword
        IF    ${condition}
            Keyword    ${arg}
            Keyword2
        END
    ```
    """

    @skip_section_if_disabled
    def visit_Section(self, node: Section) -> Section:  # noqa: N802
        return self.generic_visit(node)

    @skip_if_disabled
    def visit_KeywordCall(self, node: KeywordCall) -> KeywordCall | If:  # noqa: N802
        if not node.keyword:
            return node
        if misc.after_last_dot(misc.normalize_name(node.keyword)) == "runkeywordif":
            return misc.run_keyword_if_to_branched(
                node, self.formatting_config.separator, self.formatting_config.indent
            )
        return node
