from robocop.formatter.formatters import Formatter


class ExternalDisabledTransformer(Formatter):
    """
    This transformer is disabled by default. If it is enabled, it replaces setting names to lowercase.
    """

    ENABLED = False

    def visit_SectionHeader(self, node):  # noqa
        if not node.name:
            return node
        node.data_tokens[0].value = node.data_tokens[0].value.lower()
        return node
