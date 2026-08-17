*** Settings ***
Test Template    Log Many


*** Test Cases ***
Template data is not a keyword call
    [Tags]    robot:continue-on-failure
    Run Keyword And Continue On Failure    data

Template can be disabled
    [Tags]    robot:continue-on-failure
    [Template]    NONE
    Actual Keyword
