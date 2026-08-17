*** Settings ***
Resource    shadow.resource


*** Test Cases ***
Potentially imported wrapper
    [Tags]    robot:continue-on-failure
    Run Keyword And Continue On Failure    Should Not Be Unwrapped
    BuiltIn.Run Keyword And Continue On Failure    Explicit BuiltIn Is Safe
