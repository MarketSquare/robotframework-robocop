from robocop.checkers import VisitorChecker
from robocop.rules import RuleSeverity


class MissingKeywordName(VisitorChecker):
    """ Checker for missing keyword name. """
    rules = {
        "9903": (
            "external-rule",
            "This is external rule",
            RuleSeverity.INFO
        )
    }

    def visit_KeywordCall(self, node):  # noqa
        if node.keyword and 'Dummy' not in node.keyword:
            self.report("external-rule", node=node)
