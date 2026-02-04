from __future__ import annotations

from typing import TYPE_CHECKING

from robot.api import Token
from robot.variables.search import search_variable

from robocop.linter import sonar_qube
from robocop.linter.rules import Rule, RuleSeverity

if TYPE_CHECKING:
    from robot.parsing.model.blocks import KeywordCall


class MissingSectionVariableTypeRule(Rule):
    """
    Section variable without type annotation.

    Robot Framework 7.3 introduced type conversion for variables. This rule
    enforces that variables in the ``*** Variables ***`` section have explicit
    type annotations for better code clarity and automatic type conversion.

    This rule also checks ``VAR`` statements and assignment expressions
    (``${var} = Keyword``).

    Incorrect code example (when rule is enabled):

        *** Variables ***
        ${NUMBER}    42

        *** Keywords ***
        Example
            VAR    ${local}    value
            ${result} =    Some Keyword

    Correct code:

        *** Variables ***
        ${NUMBER: int}    42

        *** Keywords ***
        Example
            VAR    ${local: str}    value
            ${result: list} =    Some Keyword

    This rule is disabled by default.

    """

    name = "missing-section-variable-type"
    rule_id = "ANN01"
    message = "Variable '{variable_name}' is missing type annotation"
    severity = RuleSeverity.INFO
    version = ">=7.3"
    enabled = False
    added_in_version = "7.1.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CLEAR, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )


class MissingArgumentTypeRule(Rule):
    """
    Keyword argument without type annotation.

    Robot Framework 7.3 introduced type conversion for variables. This rule
    enforces that keyword arguments have explicit type annotations for better
    code clarity and automatic type conversion.

    Incorrect code example (when rule is enabled):

        *** Keywords ***
        Example
            [Arguments]    ${arg}    @{varargs}    &{kwargs}
            Log    ${arg}

    Correct code:

        *** Keywords ***
        Example
            [Arguments]    ${arg: str}    @{varargs: list}    &{kwargs: dict}
            Log    ${arg}

    This rule is disabled by default.

    """

    name = "missing-argument-type"
    rule_id = "ANN02"
    message = "Argument '{variable_name}' is missing type annotation"
    severity = RuleSeverity.INFO
    version = ">=7.3"
    enabled = False
    added_in_version = "7.1.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CLEAR, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )


class MissingForLoopVariableTypeRule(Rule):
    """
    FOR loop variable without type annotation.

    Robot Framework 7.3 introduced type conversion for variables. This rule
    enforces that FOR loop variables have explicit type annotations for better
    code clarity and automatic type conversion.

    Incorrect code example (when rule is enabled):

        *** Test Cases ***
        Example
            FOR    ${index}    IN RANGE    10
                Log    ${index}
            END

    Correct code:

        *** Test Cases ***
        Example
            FOR    ${index: int}    IN RANGE    10
                Log    ${index}
            END

    This rule is disabled by default.

    """

    name = "missing-for-loop-variable-type"
    rule_id = "ANN03"
    message = "FOR loop variable '{variable_name}' is missing type annotation"
    severity = RuleSeverity.INFO
    version = ">=7.3"
    enabled = False
    added_in_version = "7.1.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CLEAR, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )


class SetKeywordWithTypeRule(Rule):
    """
    Set Test/Suite/Global Variable keyword with variable type.

    Variable type conversion does not work with Set Test/Suite/Global Variable keywords:

        *** Keywords ***
        Set Variables
            Set Local Variable    ${variable: int}    1
            Set Suite Variable    ${variable: str}    value
            Set Test Variable    ${variable: list[str]}    value    value
            Set Task Variable    ${variable: int}    2
            Set Global Variable    ${variable: int}    3

    The VAR syntax needs to be used instead:

        *** Keywords ***
        Set Variables
            VAR    ${variable: int}    1
            VAR    ${variable: str}    value
            VAR    ${variable: list[str]}    value    value
            VAR    ${variable: int}    2
            VAR    ${variable: int}    3

    """

    name = "set-keyword-with-type"
    rule_id = "ANN04"
    message = "Set variable keyword with variable type"
    severity = RuleSeverity.ERROR
    version = ">=7.3"
    added_in_version = "8.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.DISTINCT, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    fix_suggestion = "Use VAR instead."

    def check(self, node: KeywordCall) -> None:
        if not self.enabled:
            return
        name_token = node.get_token(Token.ARGUMENT)
        if not name_token or not name_token.value:
            return
        var_match = search_variable(name_token.value, ignore_errors=True)
        if not var_match.base or ": " not in var_match.base:
            return
        keyword_token = node.get_token(Token.KEYWORD)
        self.report(
            node=keyword_token,
            lineno=keyword_token.lineno,
            col=keyword_token.col_offset + 1,
            end_col=keyword_token.col_offset + len(keyword_token.value) + 1,
        )
