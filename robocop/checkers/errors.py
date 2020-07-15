from robot.parsing.model.statements import Documentation, Comment
from robocop.checkers import VisitorChecker
from robocop.messages import MessageSeverity


def register(linter):
    linter.register_checker(ParsingErrorChecker(linter))


class ParsingErrorChecker(VisitorChecker):
    """ Checker that returns Robot Framework DataErrors as lint errors.

        Reports:
        E0401: parsing-error: Robot Framework syntax error: %s
        Configurable:
        severity: MessageSeverity
    """
    msgs = {
        "0401": (
            "parsing-error",
            "Robot Framework syntax error: %s",
            MessageSeverity.ERROR
        )
    }

    def visit_Error(self, node):
        self.report("parsing-error", node.error, node=node)
