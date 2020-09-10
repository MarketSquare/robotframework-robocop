"""
Comments checkers
"""
from robocop.checkers import VisitorChecker
from robocop.rules import RuleSeverity


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
        "0703": (
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
