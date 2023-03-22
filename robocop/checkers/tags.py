"""
Tags checkers
"""
from collections import defaultdict

from robot.api import Token

from robocop.checkers import VisitorChecker
from robocop.rules import Rule, RuleSeverity

rules = {
    "0601": Rule(
        rule_id="0601",
        name="tag-with-space",
        msg="Tag '{{ tag }}' should not contain spaces",
        severity=RuleSeverity.WARNING,
        docs="""
        Example of rule violation::
        
            Test
                [Tags]  ${tag with space}
        
        """,
    ),
    "0602": Rule(
        rule_id="0602",
        name="tag-with-or-and",
        msg="Tag '{{ tag }}' with reserved word OR/AND."
        " Hint: make sure to include this tag using lowercase name to avoid issues",
        severity=RuleSeverity.INFO,
        docs="""
        OR and AND words are used to combine tags when selecting tests to be run in Robot Framework. Using following 
        configuration::
        
            robot --include tagANDtag2
        
        Robot Framework will only execute tests that contain `tag` and `tag2`. That's why it's best to avoid AND and OR 
        in tag names. See 
        `docs <https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#tag-patterns>`_ 
        for more information.
        
        Tag matching is case-insensitive. If your tag contains OR or AND you can use lowercase to match it.
        For example, if your tag is `PORT` you can match it with `port`.
        """,
    ),
    "0603": Rule(
        rule_id="0603",
        name="tag-with-reserved-word",
        msg="Tag '{{ tag }}' prefixed with reserved word `robot:`",
        severity=RuleSeverity.WARNING,
        docs="""
        This prefix is used by Robot Framework special tags. More details 
        `here <https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#reserved-tags>`_.
        Special tags currently in use:
        
            - robot:exit
            - robot:no-dry-run
            - robot:continue-on-failure 
            - robot:recursive-continue-on-failure
            - robot:skip
            - robot:skip-on-failure
            - robot:stop-on-failure
            - robot:exclude
            - robot:private

        """,
    ),
    "0605": Rule(
        rule_id="0605",
        name="could-be-test-tags",
        msg="All tests in suite share these tags: '{{ tags }}'. "
        "You can define them in 'Test Tags' in suite settings instead",
        severity=RuleSeverity.INFO,
        docs="""
        Example::
        
            *** Test Cases ***
            Test
                [Tag]  featureX  smoke
                Step
            
            Test 2
                [Tag]  featureX
                Step
        
        In this example all tests share one common tag `featureX`. It can be declared just once using ``Test Tags``
        or ``Task Tags``.
        """,
    ),
    "0606": Rule(
        rule_id="0606",
        name="tag-already-set-in-test-tags",
        msg="Tag '{{ tag }}' is already set by {{ test_force_tags }} in suite settings",
        severity=RuleSeverity.INFO,
        docs="""
        Avoid repeating same tags in tests when the tag is already declared in ``Test Tags`` or ``Force Tags``.
        Example of rule violation::
        
            *** Setting ***
            Test Tags  common-tag
            
            *** Test Cases ***
            Test
                [Tag]  sanity  common-tag
        
        """,
    ),
    "0607": Rule(
        rule_id="0607",
        name="unnecessary-default-tags",
        msg="Tags defined in Default Tags are always overwritten",
        severity=RuleSeverity.INFO,
        docs="""
        Example of rule violation::
        
            *** Settings ***
            Default Tags  tag1  tag2
            
            *** Test Cases ***
            Test
                [Tags]  tag3
                Step
            
            Test 2
                [Tags]  tag4
                Step
        
        Since `Test` and `Test 2` have `[Tags]` section, `Default Tags` setting is never used.
        """,
    ),
    "0608": Rule(
        rule_id="0608",
        name="empty-tags",
        msg="[Tags] setting without values{{ optional_warning }}",
        severity=RuleSeverity.WARNING,
        docs="""
        If you want to use empty `[Tags]` (for example to overwrite `Default Tags`) then use `NONE` value 
        to be explicit.
        """,
    ),
    "0609": Rule(
        rule_id="0609",
        name="duplicated-tags",
        msg="Multiple tags with name '{{ name }}' (first occurrence at line {{ line }} column {{ column }})",
        severity=RuleSeverity.WARNING,
        docs="""
        Tags are free text, but they are normalized so that they are converted to lowercase and all spaces are removed.
        Only first tag is used, other occurrences are ignored.
        
        Example of duplicated tags::
        
            Test
                [Tags]    Tag    TAG    tag    t a g

        """,
    ),
}


class TagNameChecker(VisitorChecker):
    """Checker for tag names. It scans for tags with spaces or Robot Framework reserved words."""

    reports = (
        "tag-with-space",
        "tag-with-or-and",
        "tag-with-reserved-word",
        "duplicated-tags",
    )

    is_keyword = False
    reserved_tags = {
        "robot:exit",
        "robot:no-dry-run",
        "robot:continue-on-failure",
        "robot:recursive-continue-on-failure",
        "robot:skip",
        "robot:skip-on-failure",
        "robot:stop-on-failure",
        "robot:exclude",
        "robot:private",
    }

    def visit_ForceTags(self, node):  # noqa
        self.check_tags(node)

    visit_DefaultTags = visit_Tags = visit_KeywordTags = visit_ForceTags

    def visit_Documentation(self, node):  # noqa
        if self.is_keyword:
            *_, last_line = node.lines
            filtered_line = filter(
                lambda tag: tag.type not in Token.NON_DATA_TOKENS and tag.type != Token.DOCUMENTATION,
                last_line,
            )
            tags = defaultdict(list)
            for index, token in enumerate(filtered_line):
                if index == 0 and token.value.lower() != "tags:":
                    break
                token.value = token.value.rstrip(",")
                normalized_tag = token.value.lower().replace(" ", "")
                tags[normalized_tag].append(token)
                self.check_tag(token, node)
            self.check_duplicates(tags)

    def visit_Keyword(self, node):  # noqa
        self.is_keyword = True
        super().generic_visit(node)
        self.is_keyword = False

    def check_tags(self, node):
        tags = defaultdict(list)
        for tag in node.data_tokens[1:]:
            normalized_tag = tag.value.lower().replace(" ", "")
            tags[normalized_tag].append(tag)
            self.check_tag(tag, node)
        self.check_duplicates(tags)

    def check_duplicates(self, tags):
        for nodes in tags.values():
            for duplicate in nodes[1:]:
                self.report(
                    "duplicated-tags",
                    name=duplicate.value,
                    line=nodes[0].lineno,
                    column=nodes[0].col_offset + 1,
                    node=duplicate,
                    col=duplicate.col_offset + 1,
                    end_col=duplicate.end_col_offset + 1,
                )

    def check_tag(self, tag, node):
        if " " in tag.value:
            self.report(
                "tag-with-space",
                tag=tag.value,
                node=node,
                lineno=tag.lineno,
                col=tag.col_offset + 1,
                end_col=tag.end_col_offset + 1,
            )
        if "OR" in tag.value or "AND" in tag.value:
            self.report("tag-with-or-and", tag=tag.value, node=node, lineno=tag.lineno, col=tag.col_offset + 1)
        normalized = tag.value.lower()
        if normalized.startswith("robot:") and normalized not in self.reserved_tags:
            self.report(
                "tag-with-reserved-word",
                tag=tag.value,
                node=node,
                lineno=tag.lineno,
                col=tag.col_offset + 1,
                end_col=tag.end_col_offset,
            )


class TagScopeChecker(VisitorChecker):
    """Checker for tag scopes."""

    reports = (
        "could-be-test-tags",
        "tag-already-set-in-test-tags",
        "unnecessary-default-tags",
        "empty-tags",
    )

    def __init__(self):
        self.tags = []
        self.test_tags = set()
        self.default_tags = set()
        self.test_tags_node = None
        self.default_tags_node = None
        self.test_cases_count = 0
        self.in_keywords = False
        super().__init__()

    def visit_File(self, node):  # noqa
        self.tags = []
        self.test_tags = set()
        self.default_tags = set()
        self.test_cases_count = 0
        self.test_tags_node = None
        super().visit_File(node)
        if not self.tags:
            return
        if len(self.tags) != self.test_cases_count:
            return
        if self.default_tags:
            report_node = node if self.default_tags_node is None else self.default_tags_node
            self.report(
                "unnecessary-default-tags",
                node=report_node,
                col=report_node.col_offset + 1,
                end_col=report_node.get_token(Token.DEFAULT_TAGS).end_col_offset + 1,
            )
        if self.test_cases_count < 2:
            return
        common_tags = set.intersection(*[set(tags) for tags in self.tags])
        common_tags = common_tags - self.test_tags
        if common_tags:
            report_node = node if self.test_tags_node is None else self.test_tags_node
            self.report(
                "could-be-test-tags",
                tags=", ".join(common_tags),
                node=report_node,
            )

    def visit_KeywordSection(self, node):  # noqa
        self.in_keywords = True
        self.generic_visit(node)
        self.in_keywords = False

    def visit_TestCase(self, node):  # noqa
        self.test_cases_count += 1
        self.generic_visit(node)

    def visit_ForceTags(self, node):  # noqa
        self.test_tags = {token.value for token in node.data_tokens[1:]}
        self.test_tags_node = node

    def visit_DefaultTags(self, node):  # noqa
        self.default_tags = {token.value for token in node.data_tokens[1:]}
        self.default_tags_node = node

    def visit_Tags(self, node):  # noqa
        if not node.values:
            suffix = "" if self.in_keywords else ". Consider using NONE if you want to overwrite the Default Tags"
            self.report(
                "empty-tags",
                optional_warning=suffix,
                node=node,
                col=node.data_tokens[0].col_offset + 1,
                end_col=node.end_col_offset,
            )
        self.tags.append([tag.value for tag in node.data_tokens[1:]])
        for tag in node.data_tokens[1:]:
            if tag.value not in self.test_tags:
                continue
            test_force_tags = self.test_tags_node.data_tokens[0].value
            self.report(
                "tag-already-set-in-test-tags",
                tag=tag.value,
                test_force_tags=test_force_tags,
                node=node,
                lineno=tag.lineno,
                col=tag.col_offset + 1,
            )
