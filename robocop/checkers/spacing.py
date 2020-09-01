"""
Spacing checkers
"""
from robocop.checkers import RawFileChecker
from robocop.rules import RuleSeverity


def register(linter):
    linter.register_checker(InvalidSpacingChecker(linter))


class InvalidSpacingChecker(RawFileChecker):
    """ Checker for invalid spacing. """
    rules = {
        "1001": (
            "trailing-whitespace",
            "Trailing whitespace at the end of line",
            RuleSeverity.WARNING
        )
    }

    def check_line(self, line, lineno):
        stripped_line = line.rstrip('\n')
        if stripped_line:
            if stripped_line[-1] == ' ':
                self.report("trailing-whitespace", lineno=lineno, col=len(stripped_line))
