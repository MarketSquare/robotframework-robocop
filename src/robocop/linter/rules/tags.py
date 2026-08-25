"""Tags checkers"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, TypeAlias

from robot.api import Token

from robocop.linter import sonar_qube
from robocop.linter.fix import (
    Fix,
    FixApplicability,
    FixAvailability,
    TextEdit,
    remove_empty_setting_fix,
    remove_statement_fix,
)
from robocop.linter.rules import FixableRule, Rule, RuleParam, RuleSeverity, SeverityThreshold
from robocop.parsing.variables import VariableMatches  # type: ignore[attr-defined]

if TYPE_CHECKING:
    from robot.parsing import File
    from robot.parsing.model.blocks import Keyword, TestCase
    from robot.parsing.model.statements import (
        DefaultTags,
        Documentation,
        ForceTags,
        KeywordCall,
        KeywordTags,
        Statement,
        Tags,
    )

    from robocop.linter.diagnostics import Diagnostic

TagNode: TypeAlias = "ForceTags | DefaultTags | Tags | KeywordTags"

SETTING_WITH_SINGLE_TAG = 2  # the setting name token and a single tag token

CONTINUE_ON_FAILURE_TAGS = ("robot:recursive-continue-on-failure", "robot:continue-on-failure")
"""Tags enabling the continue on failure mode, ordered from the most to the least significant one."""


def _find_reported_tag(node: Statement, diag: Diagnostic) -> Token | None:
    """Find the tag token reported by the diagnostic using its position."""
    return next(
        (
            token
            for token in node.data_tokens[1:]
            if token.lineno == diag.range.start.line and token.col_offset + 1 == diag.range.start.character
        ),
        None,
    )


def _lines_without_tag(node: Statement, source_lines: list[str], tag: Token) -> list[str]:
    """
    Return the statement lines with the tag removed.

    The separator preceding the tag is removed together with it. If the tag was the only data in its line,
    the whole line is removed - unless it contains a comment, which is always preserved.
    """
    lines = source_lines[node.lineno - 1 : node.end_lineno]
    index = tag.lineno - node.lineno
    line = lines[index]
    lines[index] = line[: tag.col_offset].rstrip() + line[tag.end_col_offset :]
    only_tag_in_line = not any(token.lineno == tag.lineno for token in node.data_tokens if token is not tag)
    has_comment = any(token.lineno == tag.lineno for token in node.get_tokens(Token.COMMENT))
    if only_tag_in_line and not has_comment:
        lines.pop(index)
    return lines


def remove_tag_fix(rule: FixableRule, diag: Diagnostic, source_lines: list[str], message: str) -> Fix | None:
    """
    Create a fix that removes the redundant tag from the tag setting.

    If the removed tag is the only tag in the setting, the whole setting is removed instead. The fix replaces
    the complete statement, so that only one tag is removed in a single run - the remaining ones are reported
    and removed in the following runs.
    """
    node = diag.node
    if node is None:
        return None
    data_tokens = getattr(node, "data_tokens", [])
    if len(data_tokens) < SETTING_WITH_SINGLE_TAG:
        return None
    tag = _find_reported_tag(node, diag)
    if tag is None:
        return None
    if len(data_tokens) == SETTING_WITH_SINGLE_TAG:
        if diag.reported_arguments.get("overwrites_suite_setting"):
            # Removing the setting would apply the Default Tags instead - use the explicit NONE value.
            edit = TextEdit.replace_at_range(rule.rule_id, rule.name, diag.range, "NONE")
            return Fix(
                edits=[edit],
                message=f"{message} and replace it with an explicit NONE value",
                applicability=FixApplicability.SAFE,
            )
        return remove_statement_fix(rule, node, source_lines, message)
    edit = TextEdit.replace_lines(
        rule.rule_id, rule.name, node.lineno, node.end_lineno, "".join(_lines_without_tag(node, source_lines, tag))
    )
    return Fix(edits=[edit], message=message, applicability=FixApplicability.SAFE)


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
    severity = RuleSeverity.WARNING
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


class TagAlreadySetInTestTagsRule(FixableRule):  # TODO: support -tag
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

    The fix removes the redundant tag. If it is the only tag in the ``[Tags]`` setting, the whole setting is
    removed - unless the suite defines ``Default Tags``, in which case the explicit ``NONE`` value is used
    instead. Comments are never removed by the fix.

    """

    name = "tag-already-set-in-test-tags"
    rule_id = "TAG06"
    message = "Tag '{tag}' is already set by {test_force_tags} in suite settings"
    severity = RuleSeverity.WARNING
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.DISTINCT, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0606",)
    fix_availability = FixAvailability.ALWAYS

    def check(
        self, node: Tags, test_tags: set[str], test_tags_node: ForceTags | None, has_default_tags: bool = False
    ) -> None:
        if not self.enabled or test_tags_node is None:
            return
        test_force_tags = test_tags_node.data_tokens[0].value
        for tag in node.data_tokens[1:]:
            if tag.value not in test_tags:
                continue
            self.report(
                tag=tag.value,
                test_force_tags=test_force_tags,
                overwrites_suite_setting=has_default_tags,
                node=node,
                lineno=tag.lineno,
                col=tag.col_offset + 1,
                end_col=tag.end_col_offset + 1,
            )

    def fix(self, diag: Diagnostic, source_lines: list[str]) -> Fix | None:
        tag = diag.reported_arguments["tag"]
        return remove_tag_fix(self, diag, source_lines, f"Remove the '{tag}' tag already set in suite settings")


class UnnecessaryDefaultTagsRule(FixableRule):
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

    The fix removes the ``Default Tags`` setting. Comments are not removed.

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
    fix_availability = FixAvailability.ALWAYS

    def check(self, node: File, default_tags_node: DefaultTags | None) -> None:
        if not self.enabled:
            return
        report_node = node if default_tags_node is None else default_tags_node
        self.report(
            node=report_node,
            col=report_node.col_offset + 1,
            end_col=report_node.get_token(Token.DEFAULT_TAGS).end_col_offset + 1,
        )

    def fix(self, diag: Diagnostic, source_lines: list[str]) -> Fix | None:
        """Remove the ``Default Tags`` setting that is always overwritten."""
        node = diag.node
        if node is None or not node.data_tokens or node.data_tokens[0].type != Token.DEFAULT_TAGS:
            return None
        return remove_statement_fix(self, node, source_lines, "Remove the unnecessary 'Default Tags' setting")


class EmptyTagsRule(FixableRule):
    """
    ``[Tags]`` setting without any value.

    If you want to use empty ``[Tags]`` (for example, to overwrite ``Default Tags``), then use the ``NONE`` value
    to be explicit.

    Incorrect code example:

        *** Settings ***
        Default Tags    tag


        *** Test Cases ***
        Test without tags
            [Tags]
            Keyword Call

    Correct code example:

        *** Settings ***
        Default Tags    tag


        *** Test Cases ***
        Test without tags
            [Tags]    NONE
            Keyword Call

    The fix removes the empty ``[Tags]`` setting. If the suite defines ``Default Tags``, the test case ``[Tags]``
    is not removed but filled with the explicit ``NONE`` value instead, since the empty ``[Tags]`` overwrites the
    ``Default Tags``. Comments are never removed by the fix.

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
    fix_availability = FixAvailability.ALWAYS

    def check(self, node: Tags, in_keywords: bool, overwrites_default_tags: bool = False) -> None:
        if not self.enabled or node.values:
            return
        suffix = "" if in_keywords else ". Consider using NONE if you want to overwrite the Default Tags"
        self.report(
            optional_warning=suffix,
            overwrites_suite_setting=overwrites_default_tags,
            node=node,
            col=node.data_tokens[0].col_offset + 1,
            end_col=node.end_col_offset,
        )

    def fix(self, diag: Diagnostic, source_lines: list[str]) -> Fix | None:
        return remove_empty_setting_fix(self, diag, source_lines)


class DuplicatedTagsRule(FixableRule):
    """
    Duplicated tags found.

    Tags are free text, but they are normalized so that they are converted to lowercase and all spaces are removed.
    Only the first tag is used, other occurrences are ignored.

    Example of duplicated tags:

        *** Test Cases ***
        Test
            [Tags]    Tag    TAG    tag    t a g

    The fix removes the duplicated tags and leaves only the first occurrence. Tags defined in the keyword
    documentation are not fixed. Comments are never removed by the fix.

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
    fix_availability = FixAvailability.SOMETIMES

    def check(self, tags: dict[str, list[Token]], node: TagNode | Documentation | None = None) -> None:
        if not self.enabled:
            return
        for nodes in tags.values():
            for duplicate in nodes[1:]:
                self.report(
                    name=duplicate.value,
                    line=nodes[0].lineno,
                    column=nodes[0].col_offset + 1,
                    node=node,
                    lineno=duplicate.lineno,
                    col=duplicate.col_offset + 1,
                    end_col=duplicate.end_col_offset + 1,
                )

    def fix(self, diag: Diagnostic, source_lines: list[str]) -> Fix | None:
        node = diag.node
        if node is None or node.type == Token.DOCUMENTATION:
            return None  # tags listed in the documentation are plain text and are not fixed
        name = diag.reported_arguments["name"]
        return remove_tag_fix(self, diag, source_lines, f"Remove the duplicated '{name}' tag")


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


class TagAlreadySetInKeywordTagsRule(FixableRule):
    """
    Tag is already set in the ``Test Keyword`` setting.

    Avoid repeating the same tags in keywords when the tag is already declared in ``Keyword Tags``.
    Example of rule violation:

        *** Settings ***
        Keyword Tags  common_tag

        *** Keywords ***
        Keyword
            [Tags]  sanity  common_tag

    The fix removes the redundant tag. If it is the only tag in the ``[Tags]`` setting, the whole setting is
    removed. Comments are never removed by the fix.

    """

    name = "tag-already-set-in-keyword-tags"
    rule_id = "TAG11"
    message = "Tag '{tag}' is already set by {keyword_tags} in suite settings"
    severity = RuleSeverity.WARNING
    version = ">=6"
    added_in_version = "3.3.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.DISTINCT, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0611",)
    fix_availability = FixAvailability.ALWAYS

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

    def fix(self, diag: Diagnostic, source_lines: list[str]) -> Fix | None:
        tag = diag.reported_arguments["tag"]
        return remove_tag_fix(self, diag, source_lines, f"Remove the '{tag}' tag already set in suite settings")


class UnnecessaryContinueOnFailureRule(Rule):
    """
    ``Run Keyword And Continue On Failure`` is not needed when the continue on failure tag is set.

    ``robot:continue-on-failure`` and ``robot:recursive-continue-on-failure`` tags already make all the keywords
    in the test or keyword body run even if one of them fails. Wrapping such calls in
    ``Run Keyword And Continue On Failure`` only adds noise.

    Example of rule violation:

        *** Test Cases ***
        Test
            [Tags]    robot:continue-on-failure
            Run Keyword And Continue On Failure    Should Be Equal    ${expected}    ${actual}

    It can be rewritten to:

        *** Test Cases ***
        Test
            [Tags]    robot:continue-on-failure
            Should Be Equal    ${expected}    ${actual}

    Keyword calls nested inside ``FOR``, ``WHILE``, ``IF`` or ``TRY`` blocks are reported as well, since the tag
    also makes them continue on failure. Calls that assign a return value are ignored.

    """

    name = "unnecessary-continue-on-failure"
    rule_id = "TAG12"
    message = "'{keyword_name}' is not needed when the '{tag}' tag is used"
    severity = RuleSeverity.INFO
    added_in_version = "8.9.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CLEAR, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )

    def check(self, node: KeywordCall, name_token: Token, tag: str) -> None:
        self.report(
            keyword_name=name_token.value,
            tag=tag,
            node=node,
            lineno=name_token.lineno,
            col=name_token.col_offset + 1,
            end_col=name_token.end_col_offset + 1,
        )


class CouldBeContinueOnFailureTagRule(Rule):
    """
    Every keyword call is wrapped in ``Run Keyword And Continue On Failure``.

    If all the keyword calls in the test or keyword body are wrapped in ``Run Keyword And Continue On Failure``,
    the ``robot:continue-on-failure`` tag can be used instead. It makes the data shorter and easier to read.

    Example of rule violation:

        *** Keywords ***
        Validate Stuff
            Run Keyword And Continue On Failure    Should Be Equal    ${expected_id}    ${actual_id}
            Run Keyword And Continue On Failure    Should Be Equal    ${expected_name}    ${actual_name}

    It can be rewritten to:

        *** Keywords ***
        Validate Stuff
            [Tags]    robot:continue-on-failure
            Should Be Equal    ${expected_id}    ${actual_id}
            Should Be Equal    ${expected_name}    ${actual_name}

    Note that ``robot:continue-on-failure`` is not applied to the keywords called from the body.
    Use ``robot:recursive-continue-on-failure`` if the continue on failure mode should be inherited.

    Configure ``min_calls`` to set how many wrapped calls are required to report the rule:

        robocop check --configure could-be-continue-on-failure-tag.min_calls=3

    The rule is only reported if every keyword call in the body is wrapped. Calls nested inside ``FOR``, ``WHILE``,
    ``IF`` or ``TRY`` blocks are taken into account, since the tag affects them as well. Calls that assign a return
    value are not equivalent to the tag and prevent the rule from being reported.

    """

    name = "could-be-continue-on-failure-tag"
    rule_id = "TAG13"
    message = (
        "{block_name} '{name}' uses 'Run Keyword And Continue On Failure' {call_count} times "
        "and could use the 'robot:continue-on-failure' tag instead"
    )
    severity = RuleSeverity.INFO
    parameters = [
        RuleParam(
            name="min_calls",
            default=2,
            converter=int,
            desc="number of 'Run Keyword And Continue On Failure' calls required to report the rule",
        )
    ]
    severity_threshold = SeverityThreshold("min_calls", compare_method="greater")
    added_in_version = "8.9.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CLEAR, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )

    def check(self, node: Keyword | TestCase, block_name: str, call_count: int, other_calls: bool) -> None:
        if other_calls or call_count < self.min_calls:
            return
        self.report(
            block_name=block_name,
            name=node.name,
            call_count=call_count,
            node=node,
            end_col=node.col_offset + len(node.name) + 1,
            extended_disablers=(node.lineno, node.end_lineno),
            sev_threshold_value=call_count,
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
