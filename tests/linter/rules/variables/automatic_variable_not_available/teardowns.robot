*** Settings ***
Suite Setup    Set Local Variable    \${KEYWORD MESSAGE}    value
Test Teardown    Log Many    ${TEST STATUS}    ${TEST MESSAGE}    ${KEYWORD STATUS}
Suite Teardown    Log Many    ${SUITE STATUS}    ${SUITE MESSAGE}    ${KEYWORD MESSAGE}

*** Test Cases ***
Default Teardown Sees Later Bindings
    ${TEST STATUS} =    Set Variable    value
    Set Test Variable    \${TEST MESSAGE}    value
    Set Local Variable    \${KEYWORD STATUS}    value
    Set Suite Variable    \${SUITE STATUS}    value
    Set Global Variable    \${SUITE MESSAGE}    value

Local Teardown Sees Later Bindings
    [Teardown]    Log Many    ${TEST STATUS}    ${TEST MESSAGE}    ${KEYWORD STATUS}
    ${TEST STATUS} =    Set Variable    value
    Set Task Variable    \${TEST MESSAGE}    value
    Set Local Variable    \${KEYWORD STATUS}    value
