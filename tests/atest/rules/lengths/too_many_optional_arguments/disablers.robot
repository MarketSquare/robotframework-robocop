*** Keywords ***
Keyword
    # robocop: disable=too-many-optional-arguments
    [Arguments]    ${too}=optional  ${many}=optional
    Some keyword call
    # robocop: disable=some-rule
    Other keyword call
    # robocop: enable=some-rule
    and some more

Keyword 2
    # robocop: disable=too-many-optional-arguments
    [Arguments]    ${too}=optional  ${many}=optional
    Some keyword call
    # robocop: disable=some-rule
    Other keyword call
    # robocop: enable=some-rule
    and some more

Should Be Reported
    [Arguments]    ${too}=optional  ${many}=optional
    No Operation
