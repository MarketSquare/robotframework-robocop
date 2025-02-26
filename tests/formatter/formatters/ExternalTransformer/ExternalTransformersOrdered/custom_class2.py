from robot.api.parsing import ModelTransformer


class CustomClass2(ModelTransformer):
    def visit_SettingSection(self, node):  # noqa: N802
        node.header.data_tokens[0].value = node.header.data_tokens[0].value.upper()
        return node
