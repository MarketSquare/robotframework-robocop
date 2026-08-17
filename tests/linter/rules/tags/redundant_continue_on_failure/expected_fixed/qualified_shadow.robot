*** Test Cases ***
Qualified local shadow
    [Tags]    robot:continue-on-failure
    BuiltIn.Run Keyword And Continue On Failure    Should Not Be Unwrapped

Nested qualified local shadow
    [Tags]    robot:continue-on-failure
    BuiltIn.Run Keyword If    ${condition}    BuiltIn.Run Keyword And Continue On Failure    Still An Argument


*** Keywords ***
BuiltIn.Run Keyword And Continue On Failure
    [Arguments]    ${keyword}
    Log    ${keyword}

BuiltIn.Run Keyword If
    [Arguments]    @{arguments}
    Log    ${arguments}
