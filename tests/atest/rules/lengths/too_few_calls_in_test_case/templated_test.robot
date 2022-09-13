*** Settings ***
Documentation    Suite Documentation


*** Test Cases ***
Template Case
    [Documentation]    Documentation
    [Tags]    Tags
    [Template]    Do Stuff


*** Keywords ***
Do Stuff
    [Documentation]    Filler keyword
    [Arguments]    ${arg}    ${arg2}
    Log    ${arg}
