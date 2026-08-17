*** Test Cases ***
VAR Bindings
    Log    ${TEST STATUS}
    VAR    ${TEST STATUS}    value
    Log    ${TEST STATUS}
    VAR    ${SUITE STATUS}    value    scope=SUITE
    VAR    ${SUITE MESSAGE}    value    scope=GLOBAL

Local VAR Does Not Leak
    Log Many    ${TEST STATUS}    ${SUITE STATUS}    ${SUITE MESSAGE}
