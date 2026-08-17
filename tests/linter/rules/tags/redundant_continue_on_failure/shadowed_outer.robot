*** Test Cases ***
Nested explicit wrapper passed to shadowed run keyword
    [Tags]    robot:continue-on-failure
    Run Keyword If    ${condition}    BuiltIn.Run Keyword And Continue On Failure    Should Not Be Unwrapped


*** Keywords ***
Run Keyword If
    [Arguments]    @{arguments}
    Log    ${arguments}
