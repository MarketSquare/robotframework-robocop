*** Keywords ***
Keyword with wrapper
    [Tags]    robot:continue-on-failure
    Run Keyword And Continue On Failure    Should Be True    ${value}

Keyword with recursive tag
    [Tags]    robot:recursive-continue-on-failure
    Run Keyword And Continue On Failure
    ...    Keyword Call
    ...    argument

Keyword with assigned wrapper
    [Tags]    robot:continue-on-failure
    ${result}=    Run Keyword And Continue On Failure    Keyword Returning Value
