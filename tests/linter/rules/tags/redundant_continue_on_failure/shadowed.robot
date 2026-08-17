*** Test Cases ***
Locally shadowed wrapper
    [Tags]    robot:continue-on-failure
    Run Keyword And Continue On Failure    Should Not Be Unwrapped


*** Keywords ***
Run Keyword And Continue On Failure
    [Arguments]    ${keyword}    @{arguments}
    Log    ${keyword}: ${arguments}
