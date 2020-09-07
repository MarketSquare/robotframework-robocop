"""
Comments checkers
"""
from robocop.checkers import VisitorChecker
from robocop.rules import RuleSeverity


class CommentBaseChecker(VisitorChecker):
    """
    This is base class for comment checkers. Not supposed to be used directly.
    """
    rules = {}

    def visit_Comment(self, node):  # noqa
        self.find_comments(node)

    def visit_TestCase(self, node):  # noqa
        self.generic_visit(node)

    def visit_Keyword(self, node):  # noqa
        self.generic_visit(node)

    def visit_KeywordCall(self, node):  # noqa
        self.find_comments(node)
        self.generic_visit(node)

    def find_comments(self, node):
        for token in node.tokens:
            if token.type == 'COMMENT':
                self.comment_handler(token)

    def comment_handler(self, comment_token):
        raise NotImplementedError('CommentExplorer should not be used directly')


class CommentChecker(CommentBaseChecker):
    """ Checker for content of comments. It detects if you have leftover todo or fixme in code. """
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
        )
    }

    def comment_handler(self, comment_token):
        if 'todo' in comment_token.value.lower():
            self.report("todo-in-comment", "TODO", lineno=comment_token.lineno, col=comment_token.col_offset)
        if "fixme" in comment_token.value.lower():
            self.report("todo-in-comment", "FIXME", lineno=comment_token.lineno, col=comment_token.col_offset)
        if comment_token.value.startswith('#') and comment_token.value != '#':
            if not comment_token.value.startswith('# '):
                self.report("missing-space-after-comment", lineno=comment_token.lineno, col=comment_token.col_offset)
