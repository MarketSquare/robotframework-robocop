from robot.parsing.model.statements import Comment
from robocop.checkers import BaseChecker
from robocop.messages import MessageSeverity


def register(linter):
    linter.register_checker(CommentChecker(linter))


class CommentBaseChecker(BaseChecker):
    """
    This is base class for comment checkers. Not supposed to be used directly.
    """
    msgs = {}

    def visit_Comment(self, node):
        self.find_comments(node)

    def visit_TestCase(self, node):
        self.generic_visit(node)

    def visit_Keyword(self, node):
        self.generic_visit(node)

    def visit_KeywordCall(self, node):
        self.find_comments(node)
        self.generic_visit(node)

    def find_comments(self, node):
        for token in node.tokens:
            if token.type == 'COMMENT':
                self.comment_handler(token)

    def comment_handler(self, comment_token):
        raise NotImplementedError('CommentExplorer should not be used directly')


class CommentChecker(CommentBaseChecker):
    msgs = {
        "0701": (
            "todo-in-comment",
            "%s: ",
            MessageSeverity.WARNING
        )
    }

    def comment_handler(self, comment_token):
        if 'todo' in comment_token.value.lower():
            self.report("todo-in-comment", "TODO", lineno=comment_token.lineno, col=comment_token.col_offset)
        if "fixme" in comment_token.value.lower():
            self.report("todo-in-comment", "FIXME", lineno=comment_token.lineno, col=comment_token.col_offset)
