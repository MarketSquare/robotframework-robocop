from robot.api.parsing import Token

from robocop.formatter.formatters import Formatter


class ExampleFormatter(Formatter):
    """Formatter shipped with the example plugin. It replaces test case names with a configurable name."""

    ENABLED = False

    def __init__(self, test_name: str = "Plugin Test"):
        super().__init__()
        self.test_name = test_name

    def visit_TestCaseName(self, node):  # noqa: N802
        name_token = node.get_token(Token.TESTCASE_NAME)
        if name_token is not None:
            name_token.value = self.test_name
        return node
