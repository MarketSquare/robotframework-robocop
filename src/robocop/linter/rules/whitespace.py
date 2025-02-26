"""
Whitespace rules.

Holds rules that are used outside spacing module for now - after redesign to seperate rules/checkers spacing rules
can be moved here.
"""

from robocop.linter.rules import Rule, RuleSeverity


class NotEnoughWhitespaceAfterSettingRule(Rule):
    """
    Not enough whitespace after setting.

    Provide at least two spaces after setting.

    Incorrect code example::

        *** Test Cases ***
        Test
            [Documentation] doc
            Keyword

        *** Keywords ***
        Keyword
            [Documentation]  This is doc
            [Arguments] ${var}
            Should Be True  ${var}

    Correct code::

        *** Test Cases ***
        Test
            [Documentation]  doc
            Keyword

        *** Keywords ***
        Keyword
            [Documentation]  This is doc
            [Arguments]    ${var}
            Should Be True  ${var}

    """

    name = "not-enough-whitespace-after-setting"
    rule_id = "SPC19"
    message = "Not enough whitespace after '{setting_name}' setting"
    severity = RuleSeverity.ERROR
    added_in_version = "1.0.0"


class NotEnoughWhitespaceAfterNewlineMarkerRule(Rule):
    """
    Not enough whitespace after newline marker.

    Provide at least two spaces after newline marker.

    Incorrect code example::

        *** Variables ***
        @{LIST}  1
        ... 2
        ...  3

    Correct code::

        *** Variables ***
        @{LIST}  1
        ...  2
        ...  3

    """

    name = "not-enough-whitespace-after-newline-marker"
    rule_id = "SPC20"
    message = "Not enough whitespace after '...' marker"
    severity = RuleSeverity.ERROR
    added_in_version = "1.11.0"


class NotEnoughWhitespaceAfterVariableRule(Rule):
    """
    Not enough whitespace after variable.

    Provide at least two spaces after variable name.

    Incorrect code example::

        *** Variables ***
        ${variable} 1
        ${other_var}  2

    Correct code::

        *** Variables ***
        ${variable}  1
        ${other_var}  2

    """

    name = "not-enough-whitespace-after-variable"
    rule_id = "SPC21"
    message = "Not enough whitespace after '{variable_name}' variable name"
    severity = RuleSeverity.ERROR
    version = ">=4.0"
    added_in_version = "1.11.0"


class NotEnoughWhitespaceAfterSuiteSettingRule(Rule):
    """
    Not enough whitespace after suite setting.

    Provide at least two spaces after suite setting.

    Incorrect code example::

        *** Settings ***
        Library Collections
        Test Tags  tag
        ...  tag2
        Suite Setup Keyword

    Correct code::

        *** Settings ***
        Library    Collections
        Test Tags  tag
        ...  tag2
        Suite Setup    Keyword

    """

    name = "not-enough-whitespace-after-suite-setting"
    rule_id = "SPC22"
    message = "Not enough whitespace after '{setting_name}' setting"
    severity = RuleSeverity.ERROR
    added_in_version = "1.11.0"
