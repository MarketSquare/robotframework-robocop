*** Keywords ***
Keyword
    # robocop: off=too-many-optional-arguments
    [Arguments]    ${too}=optional  ${many}=optional
    Some keyword call
    # robocop: off=some-rule
    Other keyword call
    # robocop: on=some-rule
    and some more

Keyword 2
    # robocop: off=too-many-optional-arguments
    [Arguments]    ${too}=optional  ${many}=optional
    Some keyword call
    # robocop: off=some-rule
    Other keyword call
    # robocop: on=some-rule
    and some more

Should Be Reported
    [Arguments]    ${too}=optional  ${many}=optional
    No Operation
