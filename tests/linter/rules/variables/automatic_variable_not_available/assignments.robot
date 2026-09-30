*** Test Cases ***
Source Ordered Bindings
    Log    ${TEST STATUS}
    ${TEST STATUS} =    Set Variable    ${TEST STATUS}
    Log    ${TEST STATUS}
    BuiltIn.Set Local Variable    \${KEYWORD STATUS}    ${KEYWORD STATUS}
    Log    ${KEYWORD STATUS}
    Set Test Variable    \${TEST MESSAGE}    value
    Set Task Variable    \${KEYWORD MESSAGE}    value
    Log Many    ${TEST MESSAGE}    ${KEYWORD MESSAGE}

Bindings Do Not Leak
    Log Many    ${TEST STATUS}    ${TEST MESSAGE}    ${KEYWORD STATUS}    ${KEYWORD MESSAGE}
