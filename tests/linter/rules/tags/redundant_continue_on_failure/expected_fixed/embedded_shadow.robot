*** Test Cases ***
Embedded keyword shadows wrapper
    [Tags]    robot:continue-on-failure
    Run Keyword And Continue On Failure    Should Not Be Unwrapped


*** Keywords ***
Run Keyword And ${mode} On Failure
    [Arguments]    ${keyword}
    Log    ${mode}: ${keyword}
