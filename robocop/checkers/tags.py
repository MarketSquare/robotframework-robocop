"""
Tags checkerss
"""

from robocop.checkers import VisitorChecker
from robocop.messages import MessageSeverity


def register(linter):
    linter.register_checker(TagChecker(linter))


class TagChecker(VisitorChecker):
    """ Checker for tags. It scans for tags with spaces or Robot Framework reserved words. """
    msgs = {
        "0601": (
            "tag-with-space",
            "Tags should not contain spaces",
            MessageSeverity.WARNING
        ),
        "0602": (
            "tag-with-reserved",
            "Tag with reserved word OR/AND. Make sure to include this tag using lowercase name to avoid issues",
            MessageSeverity.INFO
        )
    }

    def visit_ForceTags(self, node):
        self.check_tags(node)

    def visit_DefaultTags(self, node):
        self.check_tags(node)

    def visit_Tags(self, node):
        self.check_tags(node)

    def check_tags(self, node):
        for tag in node.data_tokens[1:]:
            self.check_tag(tag, node)

    def check_tag(self, tag, node):
        if ' ' in tag.value:
            self.report("tag-with-space", node=node, lineno=tag.lineno, col=tag.col_offset + 1)
        if 'OR' in tag.value or 'AND' in tag.value:
            self.report("tag-with-reserved", node=node, lineno=tag.lineno, col=tag.col_offset + 1)