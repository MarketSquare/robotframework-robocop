*** Settings ***
Suite Setup        Log Many    ${TEST NAME}    ${TEST STATUS}    ${SUITE STATUS}    ${KEYWORD STATUS}
Suite Teardown     Log Many    ${SUITE STATUS}    ${SUITE MESSAGE}    ${TEST NAME}    ${KEYWORD MESSAGE}
Test Setup         Log Many    ${TEST NAME}    @{TEST TAGS}    ${TEST DOCUMENTATION}    ${TEST STATUS}
Test Teardown      Log Many    ${TEST NAME}    ${TEST STATUS}    ${TEST MESSAGE}    ${SUITE STATUS}

*** Variables ***
${NESTED_IN_VARIABLE}    value ${outer}[${KEYWORD STATUS}]
${EVERYWHERE_VARIABLE}    ${SUITE NAME}

*** Test Cases ***
Automatic Variables In Test Body
    [Setup]    Log Many    ${TEST NAME}    ${TEST STATUS}    ${KEYWORD MESSAGE}
    [Teardown]    Log Many    ${TEST NAME}    ${TEST STATUS}    ${TEST MESSAGE}    ${SUITE MESSAGE}
    Log Many    ${TEST NAME}    @{TEST TAGS}    ${TEST DOCUMENTATION}
    Log Many    ${TEST STATUS}    ${TEST MESSAGE}    ${SUITE STATUS}    ${KEYWORD STATUS}
    Log    prefix-${outer}[${KEYWORD MESSAGE}]-suffix
    Log Many    ${PREV TEST STATUS}    ${SUITE NAME}    ${LOG LEVEL}

*** Keywords ***
Caller Dependent Automatic Variables
    Log Many    ${TEST NAME}    ${TEST STATUS}    ${SUITE STATUS}    ${KEYWORD STATUS}
    [Teardown]    Log Many    ${TEST NAME}    ${TEST STATUS}    ${SUITE STATUS}    ${KEYWORD STATUS}
