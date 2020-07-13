from robot.parsing.model.statements import Documentation, Comment
from robocop.checkers import BaseChecker
from robocop.messages import MessageSeverity


def register(linter):
    linter.register_checker(ParsingErrorChecker(linter))


class ParsingErrorChecker(BaseChecker):
    msgs = {
        "0401": (
            "parsing-error",
            "Robot Framework syntax error: %s",
            MessageSeverity.ERROR
        )
    }

    def visit_Error(self, node):
        self.report("parsing-error", node.error, node=node)
