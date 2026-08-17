*** Keywords ***
Keyword with wrapper
    [Tags]    robot:continue-on-failure
    Should Be True    ${value}

Keyword with recursive tag
    [Tags]    robot:recursive-continue-on-failure
    Keyword Call
    ...    argument

Keyword with assigned wrapper
    [Tags]    robot:continue-on-failure
    ${result}=    Run Keyword And Continue On Failure    Keyword Returning Value
