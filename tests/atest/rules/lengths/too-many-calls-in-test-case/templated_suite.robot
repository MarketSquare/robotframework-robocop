*** Settings ***
Documentation    Suite Documentation
Test Template    Do Stuff


*** Test Cases ***
Template Case
    [Documentation]    Documentation
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
