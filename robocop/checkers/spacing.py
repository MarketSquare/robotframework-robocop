"""
Spacing checkers
"""
from collections import Counter
from robot.api import get_tokens
from robot.parsing.model.blocks import TestCase, Keyword, ForLoop
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
                node = empty_lines[-1]
            )


class InconsistentUseOfTabsAndSpacesChecker(VisitorChecker):
    """ Checker for inconsistent use of tabs and spaces. """

    rules = {
        "1006": (
            "mixed-tabs-and-spaces",
            "Inconsistent use of tabs and spaces in file",
            RuleSeverity.WARNING
        )
    }

    def visit_File(self, node):  # noqa
        tabs, spaces = False, False

        for token in get_tokens(node.source):
            if token.type != 'SEPARATOR':
                continue

            tabs = True if '\t' in token.value else tabs
            spaces = True if ' ' in token.value else spaces

            if tabs and spaces:
                self.report("mixed-tabs-and-spaces", node=node)
                break


class UnevenIndentChecker(VisitorChecker):
    """ Checker for uneven indendation. """
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

    @staticmethod
    def get_indent(node, column_index):
        if isinstance(node, ForLoop):
            separator = node.header.tokens[column_index]
        else:
            separator = node.tokens[column_index]
        if separator.type == 'SEPARATOR':
            return len(separator.value.expandtabs(4))
        if separator.type in ('COMMENT', 'EOL'):
            return None
        return 0

    def check_indents(self, node, req_indent=0, column_index=0):
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
            indent_len = self.get_indent(child, column_index)
            if indent_len is None:
                continue
            if hasattr(child, 'type') and child.type.strip().lower() in self.headers:
                if templated:
                    header_indents.append((indent_len, child))
                else:
                    indents.append((indent_len, child))
            else:
                indents.append((indent_len, child))
                if not column_index and (indent_len < req_indent):
                    self.report("bad-indent", node=child)
        self.validate_indent_lists(indents)
        if templated:
            self.validate_indent_lists(header_indents)

    def validate_indent_lists(self, indents):
        if len(indents) < 2:
            return
        counter = Counter(indent[0] for indent in indents)
        if len(counter) == 1:  # everything have the same indent
            return
        common_indent = counter.most_common(1)[0][0]
        for indent in indents:
            if indent[0] != common_indent:
                self.report("uneven-indent", 'over' if indent[0] > common_indent else 'under',
                            node=indent[1],
                            col=indent[0] + 1)
