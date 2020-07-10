from robot.parsing.model.statements import Documentation
from robocop.checkers import BaseChecker
from robocop.messages import MessageSeverity

MSGS = {
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


def register(linter):
    linter.register_checker(TagChecker(linter))


class TagChecker(BaseChecker):
    msgs = MSGS

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
        if 'or' in tag.value.lower() or 'and' in tag.value.lower():
            self.report("tag-with-reserved", node=node, lineno=tag.lineno, col=tag.col_offset + 1)