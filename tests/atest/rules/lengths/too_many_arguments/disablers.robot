*** Keywords ***
Keyword
    # robocop: disable=too-many-arguments
    [Arguments]    too  many
    Some keyword call
    # robocop: disable=some-rule
    Other keyword call
    # robocop: enable=some-rule
    and some more

Keyword 2
    # robocop: disable=too-many-arguments
    [Arguments]    too  many
    Some keyword call
    # robocop: disable=some-rule
    Other keyword call
    # robocop: enable=some-rule
    and some more

Should Be Reported
    [Arguments]    too  many
    No Operation
