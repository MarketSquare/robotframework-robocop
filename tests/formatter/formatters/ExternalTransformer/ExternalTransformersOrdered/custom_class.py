from robocop.formatter.formatters import Formatter


class CustomClass1(Formatter):
    def visit_SettingSection(self, node):  # noqa: N802
        node.header.data_tokens[0].value = node.header.data_tokens[0].value.lower()
        return node
