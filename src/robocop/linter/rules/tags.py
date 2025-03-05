"""Tags checkers"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from robot.api import Token

from robocop.linter.rules import Rule, RuleSeverity, VisitorChecker
from robocop.linter.utils import variable_matcher

if TYPE_CHECKING:
    from robot.parsing import File
    from robot.parsing.model.statements import Node


class TagWithSpaceRule(Rule):
    """
    Tag with space.

    When including or excluding tags, it may leads to unexpected behavior. It's recommended to use short tag names
    without spaces.

    Example of rule violation::

        *** Test Cases ***
        Test
            [Tags]  tag with space    ${tag with space}

    """

    name = "tag-with-space"
    rule_id = "TAG01"
    message = "Tag '{tag}' contains spaces"
    severity = RuleSeverity.WARNING
    added_in_version = "1.0.0"


class TagWithOrAndRule(Rule):
    """
    ``OR`` or ``AND`` keyword found in the tag.

    ``OR`` and ``AND`` words are used to combine tags when selecting tests to be run in Robot Framework. Using
    following configuration::

        robocop check --include tagANDtag2

    Robot Framework will only execute tests that contain ``tag`` and ``tag2``. That's why it's best to avoid ``AND``
    and ``OR`` in tag names. See
    `docs <https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#tag-patterns>`_
    for more information.

    Tag matching is case-insensitive. If your tag contains ``OR`` or ``AND`` you can use lowercase to match it.
    For example, if your tag is ``PORT``, you can match it with ``port``.

    """

    name = "tag-with-or-and"
    rule_id = "TAG02"
    message = "Tag '{tag}' with reserved word OR/AND"
    severity = RuleSeverity.INFO
    added_in_version = "1.0.0"


class TagWithReservedWordRule(Rule):
    """
    Tag is prefixed with reserved work ``robot:``.

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


    """

    name = "tag-with-reserved-word"
    rule_id = "TAG03"
    message = "Tag '{tag}' prefixed with reserved word `robot:`"
    severity = RuleSeverity.WARNING
    added_in_version = "1.0.0"


class CouldBeTestTagsRule(Rule):
    """
    All tests share the same tags which can be moved to ``Test Tags`` setting.

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

    Will ignore `robot:*` tags.
    """

    name = "could-be-test-tags"
    rule_id = "TAG05"
    message = "All tests in suite share these tags: '{tags}'"
    file_wide_rule = True
    severity = RuleSeverity.INFO
    added_in_version = "1.0.0"


class TagAlreadySetInTestTagsRule(Rule):
    """
    Tag is already set in the ``Test Tags`` setting.

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

    """

    name = "tag-already-set-in-test-tags"
    rule_id = "TAG06"
    message = "Tag '{tag}' is already set by {test_force_tags} in suite settings"
    severity = RuleSeverity.INFO
    added_in_version = "1.0.0"


class UnnecessaryDefaultTagsRule(Rule):
    """
    ``Default Tags`` setting is always overwritten and is unnecessary.

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

    """

    name = "unnecessary-default-tags"
    rule_id = "TAG07"
    message = "Tags defined in Default Tags are always overwritten"
    severity = RuleSeverity.INFO
    added_in_version = "1.0.0"


class EmptyTagsRule(Rule):
    """
    ``[Tags]`` setting without any value.

    If you want to use empty ``[Tags]`` (for example to overwrite ``Default Tags``) then use ``NONE`` value
    to be explicit.

    """

    name = "empty-tags"
    rule_id = "TAG08"
    message = "[Tags] setting without values{optional_warning}"
    severity = RuleSeverity.WARNING
    added_in_version = "2.0.0"


class DuplicatedTagsRule(Rule):
    """
    Duplicated tags found.

    Tags are free text, but they are normalized so that they are converted to lowercase and all spaces are removed.
    Only first tag is used, other occurrences are ignored.

    Example of duplicated tags::

        *** Test Cases ***
        Test
            [Tags]    Tag    TAG    tag    t a g

    """

    name = "duplicated-tags"
    rule_id = "TAG09"
    message = "Multiple tags with name '{name}' (first occurrence at line {line} column {column})"
    severity = RuleSeverity.WARNING
    added_in_version = "2.0.0"


class CouldBeKeywordTagsRule(Rule):
    """
    All keywords share the same tags which can be moved to ``Keyword Tags`` setting.

    Example::

        *** Keywords ***
        Keyword
            [Tags]  featureX  smoke
            Step

        Keyword
            [Tags]  featureX
            Step

    In this example all keywords share one common tag ``featureX``.It can be declared just once using
    ``Keyword Tags``.

    Will ignore `robot:*` tags.
    """

    name = "could-be-keyword-tags"
    rule_id = "TAG10"
    message = "All keywords in suite share these tags: '{tags}'"
    file_wide_rule = True
    severity = RuleSeverity.INFO
    version = ">=6"
    added_in_version = "3.3.0"


class TagAlreadySetInKeywordTagsRule(Rule):
    """
    Tag is already set in the ``Test Keyword`` setting.

    Avoid repeating the same tags in keywords when the tag is already declared in ``Keyword Tags``.
    Example of rule violation::

        *** Settings ***
        Keyword Tags  common_tag

        *** Keywords ***
        Keyword
            [Tags]  sanity  common_tag

    """

    name = "tag-already-set-in-keyword-tags"
    rule_id = "TAG11"
    message = "Tag '{tag}' is already set by {keyword_tags} in suite settings"
    severity = RuleSeverity.INFO
    version = ">=6"
    added_in_version = "3.3.0"


class TagNameChecker(VisitorChecker):
    """Checker for tag names. It scans for tags with spaces or Robot Framework reserved words."""

    tag_with_space: TagWithSpaceRule
    tag_with_or_and: TagWithOrAndRule
    tag_with_reserved_word: TagWithReservedWordRule
    duplicated_tags: DuplicatedTagsRule
    # TODO: too many tags rule

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

    def visit_ForceTags(self, node: type[Node]) -> None:  # noqa: N802
        self.check_tags(node)

    visit_DefaultTags = visit_Tags = visit_KeywordTags = visit_ForceTags  # noqa: N815

    def visit_Documentation(self, node: type[Node]) -> None:  # noqa: N802
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

    def visit_Keyword(self, node: type[Node]) -> None:  # noqa: N802
        self.is_keyword = True
        super().generic_visit(node)
        self.is_keyword = False

    def check_tags(self, node: type[Node]) -> None:
        tags = defaultdict(list)
        for tag in node.data_tokens[1:]:
            normalized_tag = tag.value.lower().replace(" ", "")
            tags[normalized_tag].append(tag)
            self.check_tag(tag, node)
        self.check_duplicates(tags)

    def check_duplicates(self, tags: defaultdict[list]) -> None:
        for nodes in tags.values():
            for duplicate in nodes[1:]:
                self.report(
                    self.duplicated_tags,
                    name=duplicate.value,
                    line=nodes[0].lineno,
                    column=nodes[0].col_offset + 1,
                    node=duplicate,
                    col=duplicate.col_offset + 1,
                    end_col=duplicate.end_col_offset + 1,
                )

    def check_tag(self, tag_token: Token, node: type[Node]) -> None:
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
                self.tag_with_reserved_word,
                tag=tag_token.value,
                node=node,
                lineno=tag_token.lineno,
                col=tag_token.col_offset + 1,
                end_col=tag_token.end_col_offset + 1,
            )

    def check_tag_substring(self, substring: str, tag: Token, node: type[Node]) -> bool:
        res = False
        if " " in substring:
            self.report(
                self.tag_with_space,
                tag=tag.value,
                node=node,
                lineno=tag.lineno,
                col=tag.col_offset + 1,
                end_col=tag.end_col_offset + 1,
            )
            res = True
        if "OR" in substring or "AND" in substring:
            self.report(
                self.tag_with_or_and,
                tag=tag.value,
                node=node,
                lineno=tag.lineno,
                col=tag.col_offset + 1,
                end_col=tag.end_col_offset + 1,
            )
            res = True
        return res


class TagScopeChecker(VisitorChecker):
    """Checker for tag scopes."""

    could_be_test_tags: CouldBeTestTagsRule
    tag_already_set_in_test_tags: TagAlreadySetInTestTagsRule
    unnecessary_default_tags: UnnecessaryDefaultTagsRule
    empty_tags: EmptyTagsRule

    def __init__(self):
        self.tags = []
        self.test_tags = set()
        self.default_tags = set()
        self.test_tags_node = None
        self.default_tags_node = None
        self.test_cases_count = 0
        self.in_keywords = False
        super().__init__()

    def visit_File(self, node: File) -> None:  # noqa: N802
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
                self.unnecessary_default_tags,
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
                self.could_be_test_tags,
                tags=", ".join(common_tags),
                node=report_node,
            )

    def visit_KeywordSection(self, node: type[Node]) -> None:  # noqa: N802
        self.in_keywords = True
        self.generic_visit(node)
        self.in_keywords = False

    def visit_TestCase(self, node: type[Node]) -> None:  # noqa: N802
        self.test_cases_count += 1
        self.generic_visit(node)

    def visit_ForceTags(self, node: type[Node]) -> None:  # noqa: N802
        self.test_tags = {token.value for token in node.data_tokens[1:]}
        self.test_tags_node = node

    def visit_DefaultTags(self, node: type[Node]) -> None:  # noqa: N802
        self.default_tags = {token.value for token in node.data_tokens[1:]}
        self.default_tags_node = node

    def visit_Tags(self, node: type[Node]) -> None:  # noqa: N802
        if not node.values:
            suffix = "" if self.in_keywords else ". Consider using NONE if you want to overwrite the Default Tags"
            self.report(
                self.empty_tags,
                optional_warning=suffix,
                node=node,
                col=node.data_tokens[0].col_offset + 1,
                end_col=node.end_col_offset,
            )
        if not self.in_keywords:
            self.tags.append([tag.value for tag in node.data_tokens[1:] if not tag.value.startswith("robot:")])
        for tag in node.data_tokens[1:]:
            if self.in_keywords or tag.value not in self.test_tags:
                continue
            test_force_tags = self.test_tags_node.data_tokens[0].value
            self.report(
                self.tag_already_set_in_test_tags,
                tag=tag.value,
                test_force_tags=test_force_tags,
                node=node,
                lineno=tag.lineno,
                col=tag.col_offset + 1,
                end_col=tag.end_col_offset + 1,
            )


class KeywordTagsChecker(VisitorChecker):
    """Checker for keyword tags."""

    could_be_keyword_tags: CouldBeKeywordTagsRule
    tag_already_set_in_keyword_tags: TagAlreadySetInKeywordTagsRule

    def __init__(self):
        self.tags_in_keywords = []
        self.keyword_tags = set()
        self.keyword_tags_node = None
        self.keywords_count = 0
        self.in_keywords = False
        super().__init__()

    def visit_File(self, node: File) -> None:  # noqa: N802
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
                self.could_be_keyword_tags,
                tags=", ".join(common_keyword_tags),
                node=report_node,
            )

    def visit_Keyword(self, node: type[Node]) -> None:  # noqa: N802
        self.keywords_count += 1
        self.generic_visit(node)

    def visit_KeywordTags(self, node: type[Node]) -> None:  # noqa: N802
        self.keyword_tags = {token.value for token in node.data_tokens[1:]}
        self.keyword_tags_node = node

    def visit_KeywordSection(self, node: type[Node]) -> None:  # noqa: N802
        self.in_keywords = True
        self.generic_visit(node)
        self.in_keywords = False

    def visit_Tags(self, node: type[Node]) -> None:  # noqa: N802
        if self.in_keywords:
            self.tags_in_keywords.append(
                [tag.value for tag in node.data_tokens[1:] if not tag.value.startswith("robot:")]
            )
        for tag in node.data_tokens[1:]:
            if not self.in_keywords or tag.value not in self.keyword_tags:
                continue
            keyword_tags = self.keyword_tags_node.data_tokens[0].value
            self.report(
                self.tag_already_set_in_keyword_tags,
                tag=tag.value,
                keyword_tags=keyword_tags,
                node=node,
                lineno=tag.lineno,
                col=tag.col_offset + 1,
                end_col=tag.end_col_offset + 1,
            )
