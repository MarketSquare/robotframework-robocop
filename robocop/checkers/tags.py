"""
Tags checkers
"""

from robocop.checkers import VisitorChecker
from robocop.rules import RuleSeverity


class TagNameChecker(VisitorChecker):
    """ Checker for tags names. It scans for tags with spaces or Robot Framework reserved words. """
    rules = {
        "0601": (
            "tag-with-space",
            "Tags should not contain spaces",
            RuleSeverity.WARNING
        ),
        "0602": (
            "tag-with-or-and",
            "Tag with reserved word OR/AND. Hint: make sure to include this tag using lowercase name to avoid issues",
            RuleSeverity.INFO
        ),
        "0603": (
            "tag-with-reserved",
            "Tag prefixed with reserved word `robot:`. Only allowed tag with this prefix is robot:no-dry-run",
            RuleSeverity.WARNING
        )
    }

    def visit_ForceTags(self, node):  # noqa
        self.check_tags(node)

    def visit_DefaultTags(self, node):  # noqa
        self.check_tags(node)

    def visit_Tags(self, node):  # noqa
        self.check_tags(node)

    def check_tags(self, node):
        for tag in node.data_tokens[1:]:
            self.check_tag(tag, node)

    def check_tag(self, tag, node):
        if ' ' in tag.value:
            self.report("tag-with-space", node=node, lineno=tag.lineno, col=tag.col_offset + 1)
        if 'OR' in tag.value or 'AND' in tag.value:
            self.report("tag-with-or-and", node=node, lineno=tag.lineno, col=tag.col_offset + 1)
        if tag.value.startswith('robot:') and tag.value != 'robot:no-dry-run':
            self.report("tag-with-reserved", node=node, lineno=tag.lineno, col=tag.col_offset + 1)


class TagScopeChecker(VisitorChecker):  # TODO: load tags also from __init__.robot
    """ Checker for tag scopes. If the all tests in suite have the same tags it will suggest using Force Tags """
    rules = {
        "0605": (
            "could-be-forced-tags",
            'All tests in suite share those tags: "%s". You can define them in Force Tags in suite settings instead',
            RuleSeverity.INFO
        ),
        "0606": (
            "tag-already-set-in-force-tags",
            "This tag is already set by Force Tags in suite settings",
            RuleSeverity.INFO
        ),
        "0607": (
            "unnecessary-default-tags",
            "Tags defined in Default Tags are always overwritten",
            RuleSeverity.INFO
        )
    }

    def __init__(self, *args):
        self.tags = []
        self.force_tags = []
        self.default_tags = []
        self.force_tags_node = None
        self.default_tags_node = None
        self.test_cases_count = 0
        super().__init__(*args)

    def visit_File(self, node):  # noqa
        self.tags = []
        self.force_tags = []
        self.default_tags = []
        self.test_cases_count = 0
        self.force_tags_node = None
        super().visit_File(node)
        if not self.tags:
            return
        if len(self.tags) != self.test_cases_count:
            return
        if self.default_tags:
            self.report("unnecessary-default-tags",
                        node=node if self.default_tags_node is None else self.default_tags_node)
        if self.test_cases_count < 2:
            return
        common_tags = set.intersection(*[set(tags) for tags in self.tags])
        common_tags = common_tags - set(self.force_tags)
        if common_tags:
            self.report("could-be-forced-tags", ', '.join(common_tags),
                        node=node if self.force_tags_node is None else self.force_tags_node)

    def visit_TestCase(self, node):  # noqa
        self.test_cases_count += 1
        self.generic_visit(node)

    def visit_ForceTags(self, node):  # noqa
        self.force_tags = [token.value for token in node.data_tokens[1:]]
        self.force_tags_node = node

    def visit_DefaultTags(self, node):  # noqa
        self.default_tags = [token.value for token in node.data_tokens[1:]]
        self.default_tags_node = node

    def visit_Tags(self, node):  # noqa
        self.tags.append([tag.value for tag in node.data_tokens[1:]])
        for tag in node.data_tokens[1:]:
            if tag.value in self.force_tags:
                self.report("tag-already-set-in-force-tags", node=node, lineno=tag.lineno, col=tag.col_offset + 1)
