"""
Miscellaneous checkers
"""
from robot.parsing.model.statements import Return, KeywordCall
from robocop.checkers import VisitorChecker
from robocop.rules import RuleSeverity


def register(linter):
    linter.register_checker(EarlyReturnChecker(linter))


class EarlyReturnChecker(VisitorChecker):
    """ Checker for keyword calls after [Return] statement. """
    rules = {
        "0901": (
            "keyword-after-return",
            "Keyword call after [Return] statement",
            RuleSeverity.ERROR
        )
    }

    def visit_Keyword(self, node):  # noqa
        returned = False
        for child in node.body:
            if isinstance(child, Return):
                returned = True
            elif isinstance(child, KeywordCall) and returned:
                self.report("keyword-after-return", node=child)
