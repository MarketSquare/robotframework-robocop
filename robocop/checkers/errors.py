"""
Errors checkers
"""
from robocop.checkers import VisitorChecker
from robocop.rules import RuleSeverity


def register(linter):
    linter.register_checker(ParsingErrorChecker(linter))


class ParsingErrorChecker(VisitorChecker):
    """ Checker that returns Robot Framework DataErrors as lint errors. """
    rules = {
        "0401": (
            "parsing-error",
            "Robot Framework syntax error: %s",
            RuleSeverity.ERROR
        )
    }

    def visit_Error(self, node):  # noqa
        self.report("parsing-error", node.error, node=node)
