from robot.api.parsing import EmptyLine, ModelTransformer


class ExternalTransformer(ModelTransformer):
    """
    This transformer add `param` number of empty lines at the end of
    *** Settings *** section.
    """

    def __init__(self, param: int = 10):
        self.param = param

    def visit_SettingSection(self, node):  # noqa
        empty_line = EmptyLine.from_params()
        node.body += [empty_line] * self.param
        return node
