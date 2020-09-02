"""
Spacing checkers
"""
from robot.parsing.model.blocks import TestCase
from robot.parsing.model.statements import EmptyLine
from robocop.checkers import RawFileChecker, VisitorChecker
from robocop.rules import RuleSeverity


def register(linter):
    linter.register_checker(InvalidSpacingChecker(linter))
    linter.register_checker(MissingTrailingBlankLineChecker(linter))


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


class MissingTrailingBlankLineChecker(VisitorChecker):
    """ Checker for invalid spacing. """
    rules = {
        "1002": (
            "missing-trailing-blank-line",
            "Missing trailing blank line at the end of file",
            RuleSeverity.WARNING
        ),
        "1003": (
            "empty-lines-between-sections",
            "Invalid number of spaces between sections (%d/%d)",
            RuleSeverity.WARNING,
            ("empty_lines_between_sections", "empty_lines_between_sections", int)
        ),
        "1004": (
            "empty-lines-between-test-cases",
            "Invalid number of spaces between test cases (%d/%d)",
            RuleSeverity.WARNING,
            ("empty_lines_between_test_cases", "empty_lines_between_test_cases", int)
        )
    }

    def __init__(self, *args):  # noqa
        self.empty_lines_between_sections = 2
        self.empty_lines_between_test_cases = 1
        super().__init__(*args)

    def visit_File(self, node):  # noqa
        for section in node.sections[:-1]:
            if not section.header:  # for comment section
                continue
            empty_lines = 0
            for child in reversed(section.body):
                if isinstance(child, TestCase):
                    for statement in reversed(child.body):
                        if isinstance(statement, EmptyLine):
                            empty_lines += 1
                        else:
                            break
                if isinstance(child, EmptyLine):
                    empty_lines += 1
                else:
                    break
            if empty_lines != self.empty_lines_between_sections:
                self.report("empty-lines-between-sections", empty_lines, self.empty_lines_between_sections,
                            lineno=section.end_lineno, col=0)
