*** Settings ***
Documentation    Suite Documentation


*** Test Cases ***
Template Case
    [Documentation]    Documentation
    [Template]    Do Stuff
    [Tags]    Tags
    ${EMPTY}     ${EMPTY}
    ${EMPTY}     ${EMPTY}
    ${EMPTY}     ${EMPTY}
    ${EMPTY}     ${EMPTY}
    ${EMPTY}     ${EMPTY}
    ${EMPTY}     ${EMPTY}
    ${EMPTY}     ${EMPTY}
    ${EMPTY}     ${EMPTY}
    ${EMPTY}     ${EMPTY}
    ${EMPTY}     ${EMPTY}
    ${EMPTY}     ${EMPTY}
    ${EMPTY}     ${EMPTY}


*** Keywords ***
Do Stuff
    [Documentation]    Filler keyword
    [Arguments]    ${arg}    ${arg2}
    Log    ${arg}
