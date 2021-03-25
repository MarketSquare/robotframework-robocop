"""
Spacing checkers
"""
from collections import Counter

from robot.api import Token
from robot.parsing.model.visitor import ModelVisitor
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
        ),
        "1010": (
            "too-many-trailing-blank-lines",
            "Too many blank lines at the end of file",
            RuleSeverity.WARNING
        )
    }

    def __init__(self, *args):
        self.raw_lines = []
        super().__init__(*args)

    def parse_file(self):
        self.raw_lines = []
        super().parse_file()
        if self.raw_lines:
            last_line = self.raw_lines[-1]
            if last_line == '\n':
                self.report("too-many-trailing-blank-lines", lineno=len(self.raw_lines) + 1, col=0)
                return
            empty_lines = 0
            for line in self.raw_lines[::-1]:
                if not line.strip():
                    empty_lines += 1
                else:
                    break
                if empty_lines > 1:
                    self.report("too-many-trailing-blank-lines", lineno=len(self.raw_lines), col=0)
                    return
            if not empty_lines and not last_line.endswith('\n'):
                self.report("missing-trailing-blank-line", lineno=len(self.raw_lines), col=0)

    def check_line(self, line, lineno):
        self.raw_lines.append(line)

        stripped_line = line.rstrip('\n')
        if stripped_line and stripped_line[-1] == ' ':
            self.report("trailing-whitespace", lineno=lineno, col=len(stripped_line))


class EmptyLinesChecker(VisitorChecker):
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
        ),
        "1009": (
            "empty-line-after-section",
            "Too many empty lines after section header (%d/%d)",
            RuleSeverity.WARNING,
            ("empty_lines", "empty_lines_after_section_header", int)
        )
    }

    def __init__(self, *args):  # noqa
        self.empty_lines_between_sections = 2
        self.empty_lines_between_test_cases = 1
        self.empty_lines_between_keywords = 1
        self.empty_lines_after_section_header = 0
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
        self.check_empty_lines_after_sections(node)
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

    def check_empty_lines_after_sections(self, node):
        for section in node.sections:
            self.check_empty_lines_after_section(section)

    def check_empty_lines_after_section(self, section):
        empty_lines = []
        for child in section.body:
            if not isinstance(child, EmptyLine):
                break
            empty_lines.append(child)
        else:
            return
        if len(empty_lines) > self.empty_lines_after_section_header:
            self.report(
                "empty-line-after-section",
                len(empty_lines),
                self.empty_lines_after_section_header,
                node=empty_lines[-1]
            )


class InconsistentUseOfTabsAndSpacesChecker(VisitorChecker, ModelVisitor):
    """ Checker for inconsistent use of tabs and spaces. """

    rules = {
        "1006": (
            "mixed-tabs-and-spaces",
            "Inconsistent use of tabs and spaces in file",
            RuleSeverity.WARNING
        )
    }

    def __init__(self, *args):
        self.found, self.tabs, self.spaces = False, False, False
        super().__init__(*args)

    def visit_File(self, node):  # noqa
        self.found, self.tabs, self.spaces = False, False, False
        super().visit_File(node)

    def visit_Statement(self, node): # noqa
        if self.found:
            return
        for token in node.get_tokens(Token.SEPARATOR):
            self.tabs = '\t' in token.value or self.tabs
            self.spaces = ' ' in token.value or self.spaces

            if self.tabs and self.spaces:
                self.report("mixed-tabs-and-spaces", node=node, lineno=1, col=0)
                self.found = True
                break


class UnevenIndentChecker(VisitorChecker):
    """ Checker for uneven indentation. """
    rules = {
        "1007": (
            "uneven-indent",
            "Line is %s-indented",
            RuleSeverity.WARNING
        ),
        "1008": (
            "bad-indent",
            "Indent expected",
            RuleSeverity.ERROR
        )
    }

    def __init__(self, *args):
        self.headers = {'arguments', 'documentation', 'setup', 'timeout', 'teardown', 'template', 'tags'}
        super().__init__(*args)

    def visit_TestCase(self, node):  # noqa
        self.check_indents(node)

    def visit_Keyword(self, node):  # noqa
        if not node.name.lstrip().startswith('#'):
            self.check_indents(node)
        self.generic_visit(node)

    def visit_ForLoop(self, node):  # noqa
        column_index = 2 if node.end is None else 0
        self.check_indents(node, node.header.tokens[1].col_offset + 1, column_index)

    def visit_For(self, node): # noqa
        column_index = 2 if node.end is None else 0
        self.check_indents(node, node.header.tokens[1].col_offset + 1, column_index)

    def visit_If(self, node):  # noqa
        column_index = 2 if node.end is None else 0
        self.check_indents(node, node.header.tokens[1].col_offset + 1, column_index)

    @staticmethod
    def get_indent(node):
        tokens = node.tokens if hasattr(node, 'tokens') else node.header.tokens
        for token in tokens:
            if token.type != Token.SEPARATOR:
                return token.col_offset
        return 0

    def check_indents(self, node, req_indent=0, column_index=0, previous_indent=None):
        indents = []
        header_indents = []
        for child in node.body:
            if hasattr(child, 'type') and child.type == 'TEMPLATE':
                templated = True
                break
        else:
            templated = False
        for child in node.body:
            if isinstance(child, EmptyLine):
                continue
            indent_len = self.get_indent(child)
            if indent_len is None:
                continue
            if hasattr(child, 'type') and child.type.strip().lower() in self.headers:
                if templated:
                    header_indents.append((indent_len, child))
                else:
                    indents.append((indent_len, child))
            else:
                if not column_index and (indent_len < req_indent):
                    self.report("bad-indent", node=child)
                else:
                    indents.append((indent_len, child))
        previous_indent = self.validate_indent_lists(indents, previous_indent)
        if templated:
            self.validate_indent_lists(header_indents)
        if getattr(node, 'orelse', None):
            self.check_indents(node.orelse, req_indent, column_index, previous_indent)

    def validate_indent_lists(self, indents, previous_indent=None):
        counter = Counter(indent[0] for indent in indents)
        if previous_indent:  # in case of continuing blocks, ie if else blocks, remember the indent
            counter += previous_indent
        if len(indents) < 2 or len(counter) == 1:  # everything have the same indent
            return counter
        common_indent = counter.most_common(1)[0][0]
        for indent in indents:
            if indent[0] != common_indent:
                self.report("uneven-indent", 'over' if indent[0] > common_indent else 'under',
                            node=indent[1],
                            col=indent[0] + 1)
        return counter


class MisalignedContinuation(VisitorChecker, ModelVisitor):
    """ Checker for misaligned continuation line markers. """
    rules = {
        "1011": (
            "misaligned-continuation",
            "Continuation marker should be aligned with starting row",
            RuleSeverity.WARNING
        )
    }

    def visit_Statement(self, node):  # noqa
        if not node.data_tokens:
            return
        new_lines = node.get_tokens(Token.CONTINUATION)
        if new_lines is None:
            return
        starting_row = node.data_tokens[0].col_offset
        for contination in new_lines:
            if contination.col_offset != starting_row:
                self.report("misaligned-continuation", lineno=contination.lineno, col=contination.col_offset+1)
