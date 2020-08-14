from robocop.checkers import VisitorChecker
from robocop.messages import MessageSeverity


def register(linter):
    linter.register_checker(SmthChecker(linter))


class SmthChecker(VisitorChecker):
    """ Checker for keyword calls after [Return] statement. """
    msgs = {
        "1101": (
            "smth",
            "Keyword call after [Return] statement",
            MessageSeverity.ERROR
        )
    }

    def visit_Keyword(self, node):  # noqa
        self.report("smth", node=node)
