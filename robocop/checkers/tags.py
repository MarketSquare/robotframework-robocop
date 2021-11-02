"""
Tags checkers
"""

from robot.api import Token

from robocop.checkers import VisitorChecker
from robocop.rules import Rule, RuleSeverity

rules = {
    "0601": Rule(
        rule_id="0601", name="tag-with-space", msg="Tag '%s' should not contain spaces", severity=RuleSeverity.WARNING
    ),
    "0602": Rule(
        rule_id="0602",
        name="tag-with-or-and",
        msg="Tag '%s' with reserved word OR/AND."
        " Hint: make sure to include this tag using lowercase name to avoid issues",
        severity=RuleSeverity.INFO,
    ),
    "0603": Rule(
        rule_id="0603",
        name="tag-with-reserved",
        msg="Tag '%s' prefixed with reserved word `robot:`. "
        "The only allowed tags with this prefix are robot:no-dry-run, "
        "robot:continue-on-failure and robot:recursive-continue-on-failure",
        severity=RuleSeverity.WARNING,
    ),
    "0605": Rule(
        rule_id="0605",
        name="could-be-forced-tags",
        msg="All tests in suite share those tags: '%s'. You can define them in Force Tags in suite settings instead",
        severity=RuleSeverity.INFO,
    ),
    "0606": Rule(
        rule_id="0606",
        name="tag-already-set-in-force-tags",
        msg="Tag '%s' is already set by Force Tags in suite settings",
        severity=RuleSeverity.INFO,
    ),
    "0607": Rule(
        rule_id="0607",
        name="unnecessary-default-tags",
        msg="Tags defined in Default Tags are always overwritten",
        severity=RuleSeverity.INFO,
    ),
    "0608": Rule(
        rule_id="0608", name="empty-tags", msg="[Tags] setting without values%s", severity=RuleSeverity.WARNING
    ),
}


class TagNameChecker(VisitorChecker):
    """Checker for tag names. It scans for tags with spaces or Robot Framework reserved words."""

    reports = (
        "tag-with-space",
        "tag-with-or-and",
        "tag-with-reserved",
    )

    is_keyword = False
    reserved_tags = {
        "robot:no-dry-run",
        "robot:continue-on-failure",
        "robot:recursive-continue-on-failure",
    }

    def visit_ForceTags(self, node):  # noqa
        self.check_tags(node)

    def visit_DefaultTags(self, node):  # noqa
        self.check_tags(node)

    def visit_Tags(self, node):  # noqa
        self.check_tags(node)

    def visit_Documentation(self, node):  # noqa
        if self.is_keyword:
            *_, last_line = node.lines
            filtered_line = filter(
                lambda tag: tag.type not in Token.NON_DATA_TOKENS and tag.type != Token.DOCUMENTATION,
                last_line,
            )
            for index, token in enumerate(filtered_line):
                if index == 0 and token.value.lower() != "tags:":
                    break
                token.value = token.value.rstrip(",")
                self.check_tag(token, node)

    def visit_Keyword(self, node):  # noqa
        self.is_keyword = True
        super().generic_visit(node)
        self.is_keyword = False

    def check_tags(self, node):
        for tag in node.data_tokens[1:]:
            self.check_tag(tag, node)

    def check_tag(self, tag, node):
        if " " in tag.value:
            self.report("tag-with-space", tag.value, node=node, lineno=tag.lineno, col=tag.col_offset + 1)
        if "OR" in tag.value or "AND" in tag.value:
            self.report("tag-with-or-and", tag.value, node=node, lineno=tag.lineno, col=tag.col_offset + 1)
        if tag.value.startswith("robot:") and tag.value not in self.reserved_tags:
            self.report(
                "tag-with-reserved",
                tag.value,
                node=node,
                lineno=tag.lineno,
                col=tag.col_offset + 1,
            )


class TagScopeChecker(VisitorChecker):
    """Checker for tag scopes. If all tests in suite have the same tags, it will suggest using `Force Tags`"""

    reports = (
        "could-be-forced-tags",
        "tag-already-set-in-force-tags",
        "unnecessary-default-tags",
        "empty-tags",
    )

    def __init__(self):
        self.tags = []
        self.force_tags = []
        self.default_tags = []
        self.force_tags_node = None
        self.default_tags_node = None
        self.test_cases_count = 0
        self.in_keywords = False
        super().__init__()

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
            self.report(
                "unnecessary-default-tags",
                node=node if self.default_tags_node is None else self.default_tags_node,
            )
        if self.test_cases_count < 2:
            return
        common_tags = set.intersection(*[set(tags) for tags in self.tags])
        common_tags = common_tags - set(self.force_tags)
        if common_tags:
            self.report(
                "could-be-forced-tags",
                ", ".join(common_tags),
                node=node if self.force_tags_node is None else self.force_tags_node,
            )

    def visit_KeywordSection(self, node):  # noqa
        self.in_keywords = True
        self.generic_visit(node)
        self.in_keywords = False

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
        if not node.values:
            suffix = "" if self.in_keywords else ". Consider using NONE if you want to overwrite the Default Tags"
            self.report("empty-tags", suffix, node=node, col=node.end_col_offset)
        self.tags.append([tag.value for tag in node.data_tokens[1:]])
        for tag in node.data_tokens[1:]:
            if tag.value in self.force_tags:
                self.report(
                    "tag-already-set-in-force-tags",
                    tag.value,
                    node=node,
                    lineno=tag.lineno,
                    col=tag.col_offset + 1,
                )
