"""
Spacing checkers
"""
from robot.parsing.model.blocks import TestCase, Keyword
from robot.parsing.model.statements import EmptyLine, Comment
from robocop.checkers import RawFileChecker, VisitorChecker
from robocop.rules import RuleSeverity


class InvalidSpacingChecker(RawFileChecker):
    """ Checker for invalid spacing. """
    rules = {
        "1001": (
            "trailing-whitespace",
            "Trailing whitespace at the end of line",
            RuleSeverity.WARNING
        ),
        "1002": (
            "missing-trailing-blank-line",
            "Missing trailing blank line at the end of file",
            RuleSeverity.WARNING
        )
    }

    def __init__(self, *args):
        self.lines = []
        super().__init__(*args)

    def parse_file(self):
        self.lines = []
        super().parse_file()
        if self.lines and not self.lines[-1].endswith('\n'):
            self.report("missing-trailing-blank-line", lineno=len(self.lines), col=0)

    def check_line(self, line, lineno):
        self.lines.append(line)

        stripped_line = line.rstrip('\n')
        if stripped_line and stripped_line[-1] == ' ':
            self.report("trailing-whitespace", lineno=lineno, col=len(stripped_line))


class MissingTrailingBlankLineChecker(VisitorChecker):
    """ Checker for invalid spacing. """
    rules = {
        "1003": (
            "empty-lines-between-sections",
            "Invalid number of empty lines between sections (%d/%d)",
            RuleSeverity.WARNING,
            ("empty_lines", "empty_lines_between_sections", int)
        ),
        "1004": (
            "empty-lines-between-test-cases",
            "Invalid number of empty lines between test cases (%d/%d)",
            RuleSeverity.WARNING,
            ("empty_lines", "empty_lines_between_test_cases", int)
        ),
        "1005": (
            "empty-lines-between-keywords",
            "Invalid number of empty lines between keywords (%d/%d)",
            RuleSeverity.WARNING,
            ("empty_lines", "empty_lines_between_keywords", int)
        )
    }

    def __init__(self, *args):  # noqa
        self.empty_lines_between_sections = 2
        self.empty_lines_between_test_cases = 1
        self.empty_lines_between_keywords = 1
        super().__init__(*args)

    def visit_TestCaseSection(self, node):  # noqa
        for child in node.body[:-1]:
            empty_lines = 0
            if not isinstance(child, TestCase):
                continue
            for token in reversed(child.body):
                if isinstance(token, EmptyLine):
                    empty_lines += 1
                elif isinstance(token, Comment):
                    continue
                else:
                    break
            if empty_lines != self.empty_lines_between_test_cases:
                self.report("empty-lines-between-test-cases", empty_lines, self.empty_lines_between_test_cases,
                            lineno=child.end_lineno, col=0)
        self.generic_visit(node)

    def visit_KeywordSection(self, node):  # noqa
        for child in node.body[:-1]:
            empty_lines = 0
            if not isinstance(child, Keyword):
                continue
            for token in reversed(child.body):
                if isinstance(token, EmptyLine):
                    empty_lines += 1
                elif isinstance(token, Comment):
                    continue
                else:
                    break
            if empty_lines != self.empty_lines_between_keywords:
                self.report("empty-lines-between-keywords", empty_lines, self.empty_lines_between_keywords,
                            lineno=child.end_lineno, col=0)
        self.generic_visit(node)

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
        super().visit_File(node)
