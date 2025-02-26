from robot.api.parsing import Token
from robot.utils.normalizing import normalize_whitespace

from robocop.formatter.disablers import skip_if_disabled, skip_section_if_disabled
from robocop.formatter.formatters import Formatter


class NormalizeSettingName(Formatter):
    """
    Normalize setting name.

    Ensure that setting names are title case without leading or trailing whitespace. For example from:

    ```robotframework
    *** Settings ***
    library    library.py
    test template    Template
    FORCE taGS    tag1

    *** Keywords ***
    Keyword
        [arguments]    ${arg}
        [ DOCUMENTATION]   Setup Keyword
    ```

    To:

    ```robotframework
    *** Settings ***
    Library    library.py
    Test Template    Template
    Force Tags    tag1

    *** Keywords ***
    Keyword
        [Arguments]    ${arg}
        [Documentation]   Setup Keyword
    ```
    """

    @skip_section_if_disabled
    def visit_Section(self, node):  # noqa: N802
        return self.generic_visit(node)

    @skip_if_disabled
    def visit_Statement(self, node):  # noqa: N802
        if node.type not in Token.SETTING_TOKENS:
            return node
        name = node.data_tokens[0].value
        if name.startswith("["):
            name = f"[{self.normalize_name(name[1:-1])}]"
        else:
            name = self.normalize_name(name)
        node.data_tokens[0].value = name
        return node

    @staticmethod
    def normalize_name(name):
        return normalize_whitespace(name).strip().title()
