*** Test Cases ***
Typed Bindings
    Log Many    ${TEST MESSAGE}    ${KEYWORD MESSAGE}
    VAR    ${TEST MESSAGE: str}    value
    ${KEYWORD MESSAGE: str} =    Set Variable    ${KEYWORD MESSAGE}
    Log Many    ${TEST MESSAGE}    ${KEYWORD MESSAGE}
