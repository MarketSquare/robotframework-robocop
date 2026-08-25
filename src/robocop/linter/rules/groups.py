"""Rules for the ``GROUP`` syntax introduced in Robot Framework 7.2."""

from __future__ import annotations

from typing import TYPE_CHECKING

from robot.api import Token

from robocop.linter import sonar_qube
from robocop.linter.rules import (
    Rule,
    RuleParam,
    RuleSeverity,
    SeverityThreshold,
)

if TYPE_CHECKING:
    from robot.parsing.model.blocks import Group


class TooFewCallsInGroupRule(Rule):
    """
    Too few keyword calls in a ``GROUP``.

    ``GROUP`` blocks are meant to group several related steps together. A group with just a single keyword call
    usually does not add any value and only introduces an extra level of indentation. Consider inlining the keyword
    or adding the missing steps:

        *** Test Cases ***
        Test
            GROUP    Login
                Log In    ${user}    ${password}    # a single keyword does not need a group
            END

    An empty ``GROUP`` is a Robot Framework syntax error and is reported by the ``parsing-error`` rule instead.

    The number of required keyword calls can be configured with the ``min_calls`` parameter:

        robocop check --configure too-few-calls-in-group.min_calls=3

    """

    name = "too-few-calls-in-group"
    rule_id = "GRP01"
    message = "GROUP '{group_name}' has too few keywords inside ({keyword_count}/{min_allowed_count})"
    severity = RuleSeverity.WARNING
    version = ">=7.2"
    parameters = [
        RuleParam(name="min_calls", default=2, converter=int, desc="number of keyword calls required in a group")
    ]
    severity_threshold = SeverityThreshold("min_calls", compare_method="less", substitute_value="min_allowed_count")
    added_in_version = "9.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.MODULAR, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )

    def check(self, node: Group, keyword_count: int) -> bool:
        """Report the rule and return whether the group has too few keyword calls."""
        if not self.enabled or keyword_count >= self.min_calls:
            return False
        group_token = node.header.get_token(Token.GROUP)
        self.report(
            group_name=node.name,
            keyword_count=keyword_count,
            min_allowed_count=self.min_calls,
            node=group_token,
            col=group_token.col_offset + 1,
            end_col=group_token.end_col_offset + 1,
            extended_disablers=(node.lineno, node.end_lineno),
            sev_threshold_value=keyword_count,
        )
        return True


class TooManyCallsInGroupRule(Rule):
    """
    Too many keyword calls in a ``GROUP``.

    A ``GROUP`` that contains a lot of keyword calls is hard to read. Consider splitting it into smaller groups or
    extracting the logic into a separate keyword.

    The number of allowed keyword calls can be configured with the ``max_calls`` parameter:

        robocop check --configure too-many-calls-in-group.max_calls=20

    """

    name = "too-many-calls-in-group"
    rule_id = "GRP02"
    message = "GROUP '{group_name}' has too many keywords inside ({keyword_count}/{max_allowed_count})"
    severity = RuleSeverity.WARNING
    version = ">=7.2"
    parameters = [
        RuleParam(name="max_calls", default=10, converter=int, desc="number of keyword calls allowed in a group")
    ]
    severity_threshold = SeverityThreshold("max_calls", compare_method="greater", substitute_value="max_allowed_count")
    added_in_version = "9.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.FOCUSED, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )

    def check(self, node: Group, keyword_count: int) -> bool:
        """Report the rule and return whether the group has too many keyword calls."""
        if not self.enabled or keyword_count <= self.max_calls:
            return False
        group_token = node.header.get_token(Token.GROUP)
        self.report(
            group_name=node.name,
            keyword_count=keyword_count,
            max_allowed_count=self.max_calls,
            node=group_token,
            col=group_token.col_offset + 1,
            end_col=group_token.end_col_offset + 1,
            extended_disablers=(node.lineno, node.end_lineno),
            sev_threshold_value=keyword_count,
        )
        return True


class GroupWithoutNameRule(Rule):
    """
    ``GROUP`` used without a name.

    A ``GROUP`` can be created without a name, but naming it documents the intent of the grouped steps and makes
    the log easier to read:

        *** Test Cases ***
        Test
            GROUP    # will be reported
                Log    message
            END

    Correct code example:

        *** Test Cases ***
        Test
            GROUP    Prepare data
                Log    message
            END

    """

    name = "group-without-name"
    rule_id = "GRP03"
    message = "GROUP does not have a name"
    severity = RuleSeverity.WARNING
    version = ">=7.2"
    added_in_version = "9.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CLEAR, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )

    def check(self, node: Group) -> None:
        """Report groups that do not have a name."""
        if not self.enabled or node.name:
            return
        group_token = node.header.get_token(Token.GROUP)
        self.report(
            node=group_token,
            col=group_token.col_offset + 1,
            end_col=group_token.end_col_offset + 1,
        )


class NestedGroupRule(Rule):
    """
    ``GROUP`` nested inside another ``GROUP``.

    Nesting groups makes the code harder to read and is rarely needed. Consider flattening the groups or extracting
    the nested group into a separate keyword:

        *** Test Cases ***
        Test
            GROUP    Outer
                GROUP    Inner    # will be reported
                    Log    message
                END
            END

    This rule is disabled by default. Enable it with ``--select nested-group``.

    """

    name = "nested-group"
    rule_id = "GRP04"
    message = "GROUP '{group_name}' is nested in another GROUP"
    severity = RuleSeverity.WARNING
    version = ">=7.2"
    enabled = False
    added_in_version = "9.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.MODULAR, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )

    def check(self, node: Group, group_depth: int) -> None:
        """Report groups that are directly or indirectly nested in another group."""
        if not self.enabled or group_depth == 0:
            return
        group_token = node.header.get_token(Token.GROUP)
        self.report(
            group_name=node.name,
            node=group_token,
            col=group_token.col_offset + 1,
            end_col=group_token.end_col_offset + 1,
        )


class GroupNotAllowedRule(Rule):
    """
    ``GROUP`` syntax is not allowed.

    The ``GROUP`` syntax was introduced in Robot Framework 7.2. Use this rule to forbid it, for example when your
    project needs to stay compatible with older Robot Framework versions or when your team decided not to use groups:

        *** Test Cases ***
        Test
            GROUP    Login    # will be reported
                Log    message
            END

    This rule is disabled by default. Enable it with ``--select group-not-allowed``.

    """

    name = "group-not-allowed"
    rule_id = "GRP05"
    message = "GROUP syntax is not allowed"
    severity = RuleSeverity.WARNING
    version = ">=7.2"
    enabled = False
    added_in_version = "9.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )

    def check(self, node: Group) -> None:
        """Report every use of the ``GROUP`` syntax."""
        if not self.enabled:
            return
        group_token = node.header.get_token(Token.GROUP)
        self.report(
            node=group_token,
            col=group_token.col_offset + 1,
            end_col=group_token.end_col_offset + 1,
        )
