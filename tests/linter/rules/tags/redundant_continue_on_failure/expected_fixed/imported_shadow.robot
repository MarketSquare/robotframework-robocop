*** Settings ***
Resource    shadow.resource


*** Test Cases ***
Potentially imported wrapper
    [Tags]    robot:continue-on-failure
    Run Keyword And Continue On Failure    Should Not Be Unwrapped
    Explicit BuiltIn Is Safe
