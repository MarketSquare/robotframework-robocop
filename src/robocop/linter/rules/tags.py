"""Tags checkers"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, TypeAlias

from robot.api import Token

from robocop.linter import sonar_qube
from robocop.linter.rules import Rule, RuleSeverity
from robocop.parsing.variables import VariableMatches  # type: ignore[attr-defined]

if TYPE_CHECKING:
    from robot.parsing import File
    from robot.parsing.model.statements import (
        DefaultTags,
        Documentation,
        ForceTags,
        KeywordTags,
        Tags,
    )

TagNode: TypeAlias = "ForceTags | DefaultTags | Tags | KeywordTags"


class TagWithSpaceRule(Rule):
    """
    Tag with space.

    When including or excluding tags, it may lead to unexpected behavior. It's recommended to use short tag names
    without spaces.

    Example of rule violation:

        *** Test Cases ***
        Test
            [Tags]  tag with space    ${tag with space}

    """

    name = "tag-with-space"
    rule_id = "TAG01"
    message = "Tag '{tag}' contains spaces"
    severity = RuleSeverity.WARNING
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0601",)

    def check(self, substring: str, tag: Token, node: TagNode | Documentation) -> bool:
        """Report the rule and return whether the tag substring contains a space."""
        if " " not in substring:
            return False
        self.report(
            tag=tag.value,
            node=node,
            lineno=tag.lineno,
            col=tag.col_offset + 1,
            end_col=tag.end_col_offset + 1,
        )
        return True


class TagWithOrAndRule(Rule):
    """
    ``OR`` or ``AND`` keyword found in the tag.

    ``OR`` and ``AND`` words are used to combine tags when selecting tests to be run in Robot Framework. Using
    the following configuration:

        robocop check --include tagANDtag2

    Robot Framework will only execute tests that contain ``tag`` and ``tag2``. That's why it's best to avoid ``AND``
    and ``OR`` in tag names. See [docs](https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#tag-patterns)
    for more information.

    Tag matching is case-insensitive. If your tag contains ``OR`` or ``AND`` you can use lowercase to match it.
    For example, if your tag is ``PORT``, you can match it with ``port``.

    """

    name = "tag-with-or-and"
    rule_id = "TAG02"
    message = "Tag '{tag}' with reserved word OR/AND"
    severity = RuleSeverity.INFO
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0602",)

    def check(self, substring: str, tag: Token, node: TagNode | Documentation) -> bool:
        """Report the rule and return whether the tag substring contains OR or AND."""
        if "OR" not in substring and "AND" not in substring:
            return False
        self.report(
            tag=tag.value,
            node=node,
            lineno=tag.lineno,
            col=tag.col_offset + 1,
            end_col=tag.end_col_offset + 1,
        )
        return True


class TagWithReservedWordRule(Rule):
    """
    Tag is prefixed with reserved work ``robot:``.

    ``robot:`` prefix is used by Robot Framework special tags. More details in
    [RF User Guide](https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#reserved-tags).
    Special tags that are currently in use:

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
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0603",)

    reserved_tags: ClassVar[set[str]] = {
        "robot:exit",
        "robot:exit-on-failure",
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

    def check(self, tag: Token, node: TagNode | Documentation, contains_variable: bool) -> None:
        if not self.enabled or contains_variable:
            return
        normalized = tag.value.lower()
        if not normalized.startswith("robot:") or normalized in self.reserved_tags:
            return
        self.report(
            tag=tag.value,
            node=node,
            lineno=tag.lineno,
            col=tag.col_offset + 1,
            end_col=tag.end_col_offset + 1,
        )


class CouldBeTestTagsRule(Rule):
    """
    All tests share the same tags which can be moved to the ``Test Tags`` setting.

    Example:

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
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0605",)

    def check(self, node: File, common_tags: set[str], test_tags_node: ForceTags | None) -> None:
        if not self.enabled or not common_tags:
            return
        report_node = node if test_tags_node is None else test_tags_node
        self.report(tags=", ".join(sorted(common_tags)), node=report_node)


class TagAlreadySetInTestTagsRule(Rule):  # TODO: support -tag
    """
    Tag is already set in the ``Test Tags`` setting.

    Avoid repeating the same tags in tests when the tag is already declared in ``Test Tags`` or ``Force Tags``.
    Example of rule violation:

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
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.DISTINCT, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0606",)

    def check(self, node: Tags, test_tags: set[str], test_tags_node: ForceTags | None) -> None:
        if not self.enabled or test_tags_node is None:
            return
        test_force_tags = test_tags_node.data_tokens[0].value
        for tag in node.data_tokens[1:]:
            if tag.value not in test_tags:
                continue
            self.report(
                tag=tag.value,
                test_force_tags=test_force_tags,
                node=node,
                lineno=tag.lineno,
                col=tag.col_offset + 1,
                end_col=tag.end_col_offset + 1,
            )


class UnnecessaryDefaultTagsRule(Rule):
    """
    ``Default Tags`` setting is always overwritten and is unnecessary.

    Example of rule violation:

        *** Settings ***
        Default Tags  tag1  tag2

        *** Test Cases ***
        Test
            [Tags]  tag3
            Step

        Test 2
            [Tags]  tag4
            Step

    Since ``Test`` and ``Test 2`` have the ``[Tags]`` section, the ``Default Tags`` setting is never used.

    """

    name = "unnecessary-default-tags"
    rule_id = "TAG07"
    message = "Tags defined in Default Tags are always overwritten"
    severity = RuleSeverity.INFO
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0607",)

    def check(self, node: File, default_tags_node: DefaultTags | None) -> None:
        if not self.enabled:
            return
        report_node = node if default_tags_node is None else default_tags_node
        self.report(
            node=report_node,
            col=report_node.col_offset + 1,
            end_col=report_node.get_token(Token.DEFAULT_TAGS).end_col_offset + 1,
        )


class EmptyTagsRule(Rule):
    """
    ``[Tags]`` setting without any value.

    If you want to use empty ``[Tags]`` (for example, to overwrite ``Default Tags``), then use the ``NONE`` value
    to be explicit.

    """

    name = "empty-tags"
    rule_id = "TAG08"
    message = "[Tags] setting without values{optional_warning}"
    severity = RuleSeverity.WARNING
    added_in_version = "2.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0608",)

    def check(self, node: Tags, in_keywords: bool) -> None:
        if not self.enabled or node.values:
            return
        suffix = "" if in_keywords else ". Consider using NONE if you want to overwrite the Default Tags"
        self.report(
            optional_warning=suffix,
            node=node,
            col=node.data_tokens[0].col_offset + 1,
            end_col=node.end_col_offset,
        )


class DuplicatedTagsRule(Rule):
    """
    Duplicated tags found.

    Tags are free text, but they are normalized so that they are converted to lowercase and all spaces are removed.
    Only the first tag is used, other occurrences are ignored.

    Example of duplicated tags:

        *** Test Cases ***
        Test
            [Tags]    Tag    TAG    tag    t a g

    """

    name = "duplicated-tags"
    rule_id = "TAG09"
    message = "Multiple tags with name '{name}' (first occurrence at line {line} column {column})"
    severity = RuleSeverity.WARNING
    added_in_version = "2.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.DISTINCT, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0609",)

    def check(self, tags: dict[str, list[Token]]) -> None:
        if not self.enabled:
            return
        for nodes in tags.values():
            for duplicate in nodes[1:]:
                self.report(
                    name=duplicate.value,
                    line=nodes[0].lineno,
                    column=nodes[0].col_offset + 1,
                    node=duplicate,
                    col=duplicate.col_offset + 1,
                    end_col=duplicate.end_col_offset + 1,
                )


class CouldBeKeywordTagsRule(Rule):
    """
    All keywords share the same tags which can be moved to the ``Keyword Tags`` setting.

    Example:

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
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0610",)

    def check(self, node: File, common_tags: set[str], keyword_tags_node: KeywordTags | None) -> None:
        if not self.enabled or not common_tags:
            return
        report_node = node if keyword_tags_node is None else keyword_tags_node
        self.report(tags=", ".join(sorted(common_tags)), node=report_node)


class TagAlreadySetInKeywordTagsRule(Rule):
    """
    Tag is already set in the ``Test Keyword`` setting.

    Avoid repeating the same tags in keywords when the tag is already declared in ``Keyword Tags``.
    Example of rule violation:

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
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.DISTINCT, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0611",)

    def check(self, node: Tags, keyword_tags: set[str], keyword_tags_node: KeywordTags | None) -> None:
        if not self.enabled or keyword_tags_node is None:
            return
        keyword_tags_name = keyword_tags_node.data_tokens[0].value
        for tag in node.data_tokens[1:]:
            if tag.value not in keyword_tags:
                continue
            self.report(
                tag=tag.value,
                keyword_tags=keyword_tags_name,
                node=node,
                lineno=tag.lineno,
                col=tag.col_offset + 1,
                end_col=tag.end_col_offset + 1,
            )


def split_tag_on_variables(tag_value: str) -> tuple[list[str], bool]:
    """Split tag value into substrings separated by variables and detect if any variable was found."""
    variable_found = False
    substrings = []
    after = tag_value
    for match in VariableMatches(tag_value, ignore_errors=True):
        substrings.append(match.before)
        variable_found = variable_found or bool(match.match)
        after = match.after
    substrings.append(after)
    return substrings, variable_found


def new_tag_token(tag_value: str, lineno: int, col_offset: int) -> Token:
    """Create new token based on tag value."""
    subtoken = Token(Token.ARGUMENT, tag_value)
    subtoken.lineno = lineno
    subtoken.col_offset = col_offset
    return subtoken
