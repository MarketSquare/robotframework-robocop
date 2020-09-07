from robocop.checkers import VisitorChecker
from robocop.rules import RuleSeverity


def register(linter):
    linter.register_checker(SmthChecker(linter))


class SmthChecker(VisitorChecker):
    """ Checker for keyword calls after [Return] statement. """
    rules = {
        "1102": (
            "smth2",
            "Keyword call after [Return] statement",
            RuleSeverity.ERROR
        )
    }

    def visit_Keyword(self, node):  # noqa
        self.report("smth", node=node)
