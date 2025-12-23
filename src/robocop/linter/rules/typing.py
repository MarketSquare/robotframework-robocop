from robocop.linter import sonar_qube
from robocop.linter.rules import Rule, RuleSeverity


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
