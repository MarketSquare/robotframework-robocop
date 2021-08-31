"""
Comments checkers
"""
from codecs import (
    BOM_UTF32_BE,
    BOM_UTF32_LE,
    BOM_UTF8,
    BOM_UTF16_LE,
    BOM_UTF16_BE
)

from robocop.checkers import RawFileChecker, VisitorChecker
from robocop.rules import RuleSeverity
from robocop.utils import IS_RF4


class CommentChecker(VisitorChecker):
    """ Checker for comments content. It detects invalid comments or leftovers like `todo` or `fixme` in the code. """
    rules = {
        "0701": (
            "todo-in-comment",
            "Found %s in comment",
            RuleSeverity.WARNING
        ),
        "0702": (
            "missing-space-after-comment",
            "Missing blank space after comment character",
            RuleSeverity.WARNING
        ),
        "0703": (  # Deprecated in RF 4.0
            "invalid-comment",
            "Invalid comment. '#' needs to be first character in the cell. "
            "For block comments you can use '*** Comments ***' section",
            RuleSeverity.ERROR
        )
    }

    def visit_Comment(self, node):  # noqa
        self.find_comments(node)

    def visit_TestCase(self, node):  # noqa
        self.check_invalid_comments(node.name, node)
        self.generic_visit(node)

    def visit_Keyword(self, node):  # noqa
        self.check_invalid_comments(node.name, node)
        self.generic_visit(node)

    def visit_KeywordCall(self, node):  # noqa
        self.find_comments(node)
        self.generic_visit(node)

    def visit_Return(self, node):  # noqa
        self.find_comments(node)
        self.generic_visit(node)

    def visit_Documentation(self, node):  # noqa
        self.find_comments(node)
        self.generic_visit(node)

    def visit_SectionHeader(self, node):  # noqa
        self.find_comments(node)
        self.generic_visit(node)

    def visit_Tags(self, node):  # noqa
        self.find_comments(node)
        self.generic_visit(node)

    def visit_Setup(self, node):  # noqa
        self.find_comments(node)
        self.generic_visit(node)

    def visit_Timeout(self, node):  # noqa
        self.find_comments(node)
        self.generic_visit(node)

    def visit_Template(self, node):  # noqa
        self.find_comments(node)
        self.generic_visit(node)

    def visit_Arguments(self, node):  # noqa
        self.find_comments(node)
        self.generic_visit(node)

    def visit_Variable(self, node):  # noqa
        self.find_comments(node)
        self.generic_visit(node)

    def visit_Metadata(self, node):  # noqa
        self.find_comments(node)
        self.generic_visit(node)

    def visit_ForceTags(self, node):  # noqa
        self.find_comments(node)
        self.generic_visit(node)

    def visit_DefaultTags(self, node):  # noqa
        self.find_comments(node)
        self.generic_visit(node)

    def visit_IfHeader(self, node):  # noqa
        self.find_comments(node)
        self.generic_visit(node)

    def visit_ElseHeader(self, node):  # noqa
        self.find_comments(node)
        self.generic_visit(node)

    def visit_ForHeader(self, node):  # noqa
        self.find_comments(node)
        self.generic_visit(node)

    def visit_ForLoopHeader(self, node):  # noqa
        self.find_comments(node)
        self.generic_visit(node)

    def visit_TestSetup(self, node):  # noqa
        self.find_comments(node)
        self.generic_visit(node)

    def visit_TestTeardown(self, node):  # noqa
        self.find_comments(node)
        self.generic_visit(node)

    def visit_SuiteSetup(self, node):  # noqa
        self.find_comments(node)
        self.generic_visit(node)

    def visit_SuiteTeardown(self, node):  # noqa
        self.find_comments(node)
        self.generic_visit(node)

    def visit_TestTemplate(self, node):  # noqa
        self.find_comments(node)
        self.generic_visit(node)

    def visit_TestTimeout(self, node):  # noqa
        self.find_comments(node)
        self.generic_visit(node)

    def find_comments(self, node):
        for token in node.tokens:
            if token.type == 'COMMENT':
                self.check_comment_content(token)

    def check_invalid_comments(self, name, node):
        if IS_RF4:
            return
        if name and name.lstrip().startswith('#'):
            self.report("invalid-comment", node=node, col=node.col_offset)

    def check_comment_content(self, comment_token):
        if 'todo' in comment_token.value.lower():
            self.report("todo-in-comment", "TODO", lineno=comment_token.lineno, col=comment_token.col_offset)
        if "fixme" in comment_token.value.lower():
            self.report("todo-in-comment", "FIXME", lineno=comment_token.lineno, col=comment_token.col_offset)
        if comment_token.value.startswith('#') and comment_token.value != '#':
            if not comment_token.value.startswith('# '):
                self.report("missing-space-after-comment", lineno=comment_token.lineno, col=comment_token.col_offset)


class IgnoredDataChecker(RawFileChecker):
    """ Checker for ignored data. """
    rules = {
        "0704": (
            "ignored-data",
            "Ignored data found in file",
            RuleSeverity.WARNING
        ),
        "0705": (
            "bom-encoding-in-file",
            "This file contains BOM (Byte Order Mark) encoding not supported by Robot Framework",
            RuleSeverity.WARNING
        )
    }
    BOM = [
        BOM_UTF32_BE,
        BOM_UTF32_LE,
        BOM_UTF8,
        BOM_UTF16_LE,
        BOM_UTF16_BE
    ]

    def __init__(self):
        self.is_bom = False
        super().__init__()

    def parse_file(self):
        self.is_bom = False
        if self.lines is not None:
            self._parse_lines(self.lines)
        else:
            self.detect_bom(self.source)
            with open(self.source) as file:
                self._parse_lines(file)

    def _parse_lines(self, lines):
        for lineno, line in enumerate(lines, 1):
            if self.check_line(line, lineno):
                break

    def check_line(self, line, lineno):
        if line.startswith('***'):
            return True
        if not line.startswith('# robocop:'):
            if lineno == 1 and self.is_bom:
                # if it's BOM encoded file, first line can be ignored
                return '***' in line
            self.report("ignored-data", lineno=lineno, col=0)
            return True
        return False

    def detect_bom(self, source):
        with open(source, 'rb') as raw_file:
            first_four = raw_file.read(4)
            self.is_bom = any(first_four.startswith(bom_marker) for bom_marker in IgnoredDataChecker.BOM)
            if self.is_bom:
                self.report("bom-encoding-in-file", lineno=1, col=0)
