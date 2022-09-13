*** Settings ***
Documentation    Suite Documentation
Test Template    Do Stuff


*** Test Cases ***
Template Case
    [Documentation]    Documentation
    [Tags]    Tags


*** Keywords ***
Do Stuff
    [Documentation]    Filler keyword
    [Arguments]    ${arg}    ${arg2}
    Log    ${arg}
