"""
Comments checkers
"""
from robocop.checkers import RawFileChecker, VisitorChecker
from robocop.rules import RuleSeverity
from robocop.utils import IS_RF4


class CommentChecker(VisitorChecker):
    """ Checker for content of comments. It detects invalid comments or leftover `todo` or `fixme` in code. """
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
        )
    }

    def parse_file(self):
        with open(self.source) as file:
            for lineno, line in enumerate(file, 1):
                if self.check_line(line, lineno):
                    break

    def check_line(self, line, lineno):
        if line.startswith('***'):
            return True
        if not line.startswith('***') and not line.startswith('# robocop:'):
            self.report("ignored-data", lineno=lineno, col=0)
            return True
