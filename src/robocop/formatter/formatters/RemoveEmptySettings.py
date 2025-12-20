from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from robot.api.parsing import Token

from robocop.exceptions import InvalidParameterValueError
from robocop.formatter.disablers import skip_section_if_disabled
from robocop.formatter.formatters import Formatter

if TYPE_CHECKING:
    from robot.parsing.model.blocks import File, Section
    from robot.parsing.model.statements import Statement


# TODO: preserve comments?
class RemoveEmptySettings(Formatter):
    """
    Remove empty settings.

    You can configure which settings are affected by parameter ``work_mode``. Possible values:
        - overwrite_ok (default): does not remove settings that are overwriting suite settings (Test Setup,
          Test Teardown, Test Template, Test Timeout or Default Tags)
        - always : works on every setting

    Empty settings that are overwriting suite settings will be converted to be more explicit
    (given that there is related suite settings present):

    ```robotframework
    *** Keywords ***
    Keyword
    No timeout
        [Documentation]    Empty timeout means no timeout even when Test Timeout has been used.
        [Timeout]
    ```

    To:
    ```robotframework
    *** Keywords ***
    No timeout
        [Documentation]    Disabling timeout with NONE works too and is more explicit.
        [Timeout]    NONE
    ```

    You can disable that behavior by changing ``more_explicit`` parameter value to ``False``.
    """

    def __init__(self, work_mode: str = "overwrite_ok", more_explicit: bool = True):
        super().__init__()
        if work_mode not in ("overwrite_ok", "always"):
            raise InvalidParameterValueError(
                self.__class__.__name__, "work_mode", work_mode, "Possible values:\n    overwrite_ok\n    always"
            )
        self.work_mode = work_mode
        self.more_explicit = more_explicit
        self.overwritten_settings: set[str] = set()
        self.child_types = {
            Token.SETUP,
            Token.TEARDOWN,
            Token.TIMEOUT,
            Token.TEMPLATE,
            Token.TAGS,
        }

    @skip_section_if_disabled
    def visit_Section(self, node: Section) -> Section:  # noqa: N802
        return self.generic_visit(node)

    def visit_Statement(self, node: Statement) -> Statement | None:  # noqa: N802
        # when not setting type or setting type but not empty
        if node.type not in Token.SETTING_TOKENS or len(node.data_tokens) != 1:
            return node
        if self.disablers.is_node_disabled("RemoveEmptySettings", node):  # type: ignore[union-attr]
            return node
        # when empty and not overwriting anything - remove
        if (
            node.type not in self.child_types
            or self.work_mode == "always"
            or node.type not in self.overwritten_settings
        ):
            return None
        if self.more_explicit:
            indent = node.tokens[0].value if node.tokens[0].type == Token.SEPARATOR else ""
            setting_token = node.data_tokens[0]
            node.tokens = [
                Token(Token.SEPARATOR, indent),
                setting_token,
                Token(Token.SEPARATOR, self.formatting_config.separator),  # type: ignore[union-attr]
                Token(Token.ARGUMENT, "NONE"),
                Token(Token.EOL, "\n"),
            ]
        return node

    def visit_File(self, node: File) -> None:  # noqa: N802
        if self.work_mode == "overwrite_ok":
            self.overwritten_settings = self.find_overwritten_settings(node)
        self.generic_visit(node)
        self.overwritten_settings = set()

    @staticmethod
    def find_overwritten_settings(node: File) -> set[str]:
        auto_detector = FindSuiteSettings()
        auto_detector.visit(node)
        return auto_detector.suite_settings


class FindSuiteSettings(ast.NodeVisitor):
    def __init__(self) -> None:
        self.suite_settings: set[str] = set()

    def check_setting(self, node: Statement, overwritten_type: str) -> None:
        if len(node.data_tokens) != 1:
            self.suite_settings.add(overwritten_type)

    def visit_TestSetup(self, node: Statement) -> None:
        self.check_setting(node, Token.SETUP)

    def visit_TestTeardown(self, node: Statement) -> None:
        self.check_setting(node, Token.TEARDOWN)

    def visit_TestTemplate(self, node: Statement) -> None:
        self.check_setting(node, Token.TEMPLATE)

    def visit_TestTimeout(self, node: Statement) -> None:
        self.check_setting(node, Token.TIMEOUT)

    def visit_DefaultTags(self, node: Statement) -> None:
        self.check_setting(node, Token.TAGS)
