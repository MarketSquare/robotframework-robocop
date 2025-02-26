from robot.api import Token

from robocop.formatter.formatters import Formatter


class CustomClass1(Formatter):
    def visit_SettingSection(self, node):  # noqa: N802
        node.header.data_tokens[0].value = node.header.data_tokens[0].value.lower()
        return node


class CustomClass2(Formatter):
    def __init__(self, extra_param: bool = False):
        self.extra_param = extra_param
        super().__init__()

    def visit_TestCaseName(self, node):  # noqa: N802
        """If extra_param is set to True, lower case the test case name."""
        if not self.extra_param:
            return node
        token = node.get_token(Token.TESTCASE_NAME)
        token.value = token.value.lower()
        return node
