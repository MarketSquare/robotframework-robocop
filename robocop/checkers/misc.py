"""
Miscellaneous checkers
"""
from robot.parsing.model.statements import Return, KeywordCall
from robocop.checkers import VisitorChecker
from robocop.rules import RuleSeverity
from robocop.utils import normalize_robot_name


def register(linter):
    linter.register_checker(EarlyReturnChecker(linter))


class EarlyReturnChecker(VisitorChecker):
    """ Checker for keyword calls after [Return] statement. """
    rules = {
        "0901": (
            "keyword-after-return",
            "Keyword call after %s statement",
            RuleSeverity.ERROR
        )
    }

    def visit_Keyword(self, node):  # noqa
        returned = ''
        for child in node.body:
            if isinstance(child, Return):
                returned = '[Return]'
            elif isinstance(child, KeywordCall):
                if returned:
                    self.report("keyword-after-return", returned, node=child)
                if normalize_robot_name(child.keyword) == 'returnfromkeyword':
                    returned = 'Return From Keyword'

