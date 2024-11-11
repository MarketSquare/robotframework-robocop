"""Tags checkers"""

from collections import defaultdict

from robot.api import Token

from robocop.checkers import VisitorChecker
from robocop.rules import DefaultRule, RuleSeverity
from robocop.utils import variable_matcher

RULE_CATEGORY_ID = "06"

rules = {
    "0601": DefaultRule(
        rule_id="0601",
        name="tag-with-space",
        msg="Tag '{{ tag }}' should not contain spaces",
        severity=RuleSeverity.WARNING,
        docs="""
        Example of rule violation::

            Test
                [Tags]  ${tag with space}

        """,
        added_in_version="1.0.0",
    ),
    "0602": DefaultRule(
        rule_id="0602",
        name="tag-with-or-and",
        msg="Tag '{{ tag }}' with reserved word OR/AND."
        " Hint: make sure to include this tag using lowercase name to avoid issues",
        severity=RuleSeverity.INFO,
        docs="""
        ``OR`` and ``AND`` words are used to combine tags when selecting tests to be run in Robot Framework. Using following
        configuration::

            robot --include tagANDtag2

        Robot Framework will only execute tests that contain ``tag`` and ``tag2``. That's why it's best to avoid ``AND`` and ``OR``
        in tag names. See
        `docs <https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#tag-patterns>`_
        for more information.

        Tag matching is case-insensitive. If your tag contains ``OR`` or ``AND`` you can use lowercase to match it.
        For example, if your tag is ``PORT``, you can match it with ``port``.
        """,
        added_in_version="1.0.0",
    ),
    "0603": DefaultRule(
        rule_id="0603",
        name="tag-with-reserved-word",
        msg="Tag '{{ tag }}' prefixed with reserved word `robot:`",
        severity=RuleSeverity.WARNING,
        docs="""
        ``robot:`` prefix is used by Robot Framework special tags. More details
        `here <https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#reserved-tags>`_.
        Special tags currently in use:

            - robot:exit
            - robot:flatten
            - robot:no-dry-run
            - robot:continue-on-failure
            - robot:recursive-continue-on-failure
            - robot:skip
            - robot:skip-on-failure
            - robot:stop-on-failure
            - robot:recursive-stop-on-failure
            - robot:exclude
            - robot:private

        """,
        added_in_version="1.0.0",
    ),
    "0605": DefaultRule(
        rule_id="0605",
        name="could-be-test-tags",
        msg="All tests in suite share these tags: '{{ tags }}'. "
        "You can define them in 'Test Tags' in suite settings instead",
        severity=RuleSeverity.INFO,
        docs="""
        Example::

            *** Test Cases ***
            Test
                [Tags]  featureX  smoke
                Step

            Test 2
                [Tags]  featureX
                Step

        In this example all tests share one common tag ``featureX``. It can be declared just once using ``Test Tags``
        or ``Task Tags``.
        This rule was renamed from ``could-be-force-tags`` to ``could-be-test-tags`` in Robocop 2.6.0.
        """,
        added_in_version="1.0.0",
    ),
    "0606": DefaultRule(
        rule_id="0606",
        name="tag-already-set-in-test-tags",
        msg="Tag '{{ tag }}' is already set by {{ test_force_tags }} in suite settings",
        severity=RuleSeverity.INFO,
        docs="""
        Avoid repeating the same tags in tests when the tag is already declared in ``Test Tags`` or ``Force Tags``.
        Example of rule violation::

            *** Settings ***
            Test Tags  common_tag

            *** Test Cases ***
            Test
                [Tags]  sanity  common_tag
                Some Keyword

        This rule was renamed from ``tag-already-set-in-force-tags`` to ``tag-already-set-in-test-tags`` in
        Robocop 2.6.0.
        """,
        added_in_version="1.0.0",
    ),
    "0607": DefaultRule(
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

        Since ``Test`` and ``Test 2`` have ``[Tags]`` section, ``Default Tags`` setting is never used.
        """,
        added_in_version="1.0.0",
    ),
    "0608": DefaultRule(
        rule_id="0608",
        name="empty-tags",
        msg="[Tags] setting without values{{ optional_warning }}",
        severity=RuleSeverity.WARNING,
        docs="""
        If you want to use empty ``[Tags]`` (for example to overwrite ``Default Tags``) then use ``NONE`` value
        to be explicit.
        """,
        added_in_version="2.0.0",
    ),
    "0609": DefaultRule(
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
        added_in_version="2.0.0",
    ),
    "0610": DefaultRule(
        rule_id="0610",
        name="could-be-keyword-tags",
        msg="All keywords in suite share these tags: '{{ tags }}'. "
        "You can define them in 'Keyword Tags' in suite settings instead",
        severity=RuleSeverity.INFO,
        version=">=6",
        docs="""
        Example::

            *** Keywords ***
            Keyword
                [Tags]  featureX  smoke
                Step

            Keyword 2
                [Tags]  featureX
                Step

        In this example all keywords share one common tag ``featureX``. It can be declared just once using ``Keyword Tags``.
        """,
        added_in_version="3.3.0",
    ),
    "0611": DefaultRule(
        rule_id="0611",
        name="tag-already-set-in-keyword-tags",
        msg="Tag '{{ tag }}' is already set by {{ keyword_tags }} in suite settings",
        severity=RuleSeverity.INFO,
        version=">=6",
        docs="""
        Avoid repeating the same tags in keywords when the tag is already declared in ``Keyword Tags``.
        Example of rule violation::

            *** Settings ***
            Keyword Tags  common_tag

            *** Keywords ***
            Keyword
                [Tags]  sanity  common_tag
        """,
        added_in_version="3.3.0",
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
        "robot:flatten",
        "robot:no-dry-run",
        "robot:continue-on-failure",
        "robot:recursive-continue-on-failure",
        "robot:skip",
        "robot:skip-on-failure",
        "robot:stop-on-failure",
        "robot:recursive-stop-on-failure",
        "robot:exclude",
        "robot:private",
    }

    def visit_ForceTags(self, node):  # noqa: N802
        self.check_tags(node)

    visit_DefaultTags = visit_Tags = visit_KeywordTags = visit_ForceTags  # noqa: N815

    def visit_Documentation(self, node):  # noqa: N802
        """
        Parse tags from last line of documentation.

        Tags can be defined as comma separated list - Tags: tag1, tag2 .
        """
        if not self.is_keyword:
            return
        *_, last_line = node.lines
        args = [tag for tag in last_line if tag.type == Token.ARGUMENT]
        if not args or not args[0].value.lower().startswith("tags:"):
            return
        duplicates = defaultdict(list)
        for index, token in enumerate(args):
            tags = token.value
            col_start = token.col_offset
            if index == 0:
                tags = tags[len("tags:") :]
                col_start += len("tags:")
            for tag in tags.split(","):
                stripped_tag = tag.strip()
                if not stripped_tag:
                    continue
                normalized = stripped_tag.lower().replace(" ", "")
                subtoken = self._get_new_tag_token(stripped_tag, token.lineno, col_start)
                col_start += len(tag) + 1  # 1 for ,
                duplicates[normalized].append(subtoken)
                self.check_tag(subtoken, node)
        self.check_duplicates(duplicates)

    def _get_new_tag_token(self, tag_value: str, lineno: int, col_offset: int) -> Token:
        """Create new token based on tag value."""
        subtoken = Token(Token.ARGUMENT, tag_value)
        subtoken.lineno = lineno
        subtoken.col_offset = col_offset
        return subtoken

    def visit_Keyword(self, node):  # noqa: N802
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

    def check_tag(self, tag_token, node):
        var_found = False
        substrings = []
        after = tag_token.value
        for match in variable_matcher.VariableMatches(tag_token.value, ignore_errors=True):
            substrings.append(match.before)
            var_found = var_found or bool(match.match)
            after = match.after
        substrings.append(after)
        for substring in substrings:
            if self.check_tag_substring(substring, tag_token, node):
                break
        normalized = tag_token.value.lower()
        if not var_found and normalized.startswith("robot:") and normalized not in self.reserved_tags:
            self.report(
                "tag-with-reserved-word",
                tag=tag_token.value,
                node=node,
                lineno=tag_token.lineno,
                col=tag_token.col_offset + 1,
                end_col=tag_token.end_col_offset,
            )

    def check_tag_substring(self, substring, tag, node) -> bool:
        res = False
        if " " in substring:
            self.report(
                "tag-with-space",
                tag=tag.value,
                node=node,
                lineno=tag.lineno,
                col=tag.col_offset + 1,
                end_col=tag.end_col_offset + 1,
            )
            res = True
        if "OR" in substring or "AND" in substring:
            self.report("tag-with-or-and", tag=tag.value, node=node, lineno=tag.lineno, col=tag.col_offset + 1)
            res = True
        return res


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

    def visit_File(self, node):  # noqa: N802
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

    def visit_KeywordSection(self, node):  # noqa: N802
        self.in_keywords = True
        self.generic_visit(node)
        self.in_keywords = False

    def visit_TestCase(self, node):  # noqa: N802
        self.test_cases_count += 1
        self.generic_visit(node)

    def visit_ForceTags(self, node):  # noqa: N802
        self.test_tags = {token.value for token in node.data_tokens[1:]}
        self.test_tags_node = node

    def visit_DefaultTags(self, node):  # noqa: N802
        self.default_tags = {token.value for token in node.data_tokens[1:]}
        self.default_tags_node = node

    def visit_Tags(self, node):  # noqa: N802
        if not node.values:
            suffix = "" if self.in_keywords else ". Consider using NONE if you want to overwrite the Default Tags"
            self.report(
                "empty-tags",
                optional_warning=suffix,
                node=node,
                col=node.data_tokens[0].col_offset + 1,
                end_col=node.end_col_offset,
            )
        if not self.in_keywords:
            self.tags.append([tag.value for tag in node.data_tokens[1:]])
        for tag in node.data_tokens[1:]:
            if self.in_keywords or tag.value not in self.test_tags:
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


class KeywordTagsChecker(VisitorChecker):
    """Checker for keyword tags."""

    reports = (
        "could-be-keyword-tags",
        "tag-already-set-in-keyword-tags",
    )

    def __init__(self):
        self.tags_in_keywords = []
        self.keyword_tags = set()
        self.keyword_tags_node = None
        self.keywords_count = 0
        self.in_keywords = False
        super().__init__()

    def visit_File(self, node):  # noqa: N802
        self.tags_in_keywords = []
        self.keyword_tags = set()
        self.keyword_tags_node = None
        self.keywords_count = 0
        super().visit_File(node)
        if not self.tags_in_keywords:
            return
        if len(self.tags_in_keywords) != self.keywords_count:
            return
        if self.keywords_count < 2:
            return
        common_keyword_tags = set.intersection(*[set(tags) for tags in self.tags_in_keywords])
        common_keyword_tags = common_keyword_tags - self.keyword_tags
        if common_keyword_tags:
            report_node = node if self.keyword_tags_node is None else self.keyword_tags_node
            self.report(
                "could-be-keyword-tags",
                tags=", ".join(common_keyword_tags),
                node=report_node,
            )

    def visit_Keyword(self, node):  # noqa: N802
        self.keywords_count += 1
        self.generic_visit(node)

    def visit_KeywordTags(self, node):  # noqa: N802
        self.keyword_tags = {token.value for token in node.data_tokens[1:]}
        self.keyword_tags_node = node

    def visit_KeywordSection(self, node):  # noqa: N802
        self.in_keywords = True
        self.generic_visit(node)
        self.in_keywords = False

    def visit_Tags(self, node):  # noqa: N802
        if self.in_keywords:
            self.tags_in_keywords.append([tag.value for tag in node.data_tokens[1:]])
        for tag in node.data_tokens[1:]:
            if not self.in_keywords or tag.value not in self.keyword_tags:
                continue
            keyword_tags = self.keyword_tags_node.data_tokens[0].value
            self.report(
                "tag-already-set-in-keyword-tags",
                tag=tag.value,
                keyword_tags=keyword_tags,
                node=node,
                lineno=tag.lineno,
                col=tag.col_offset + 1,
            )
