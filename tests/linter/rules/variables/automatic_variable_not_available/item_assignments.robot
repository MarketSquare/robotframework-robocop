*** Test Cases ***
Item Assignment Does Not Bind Base
    Log    ${TEST MESSAGE}
    ${TEST MESSAGE}[0] =    Set Variable    value
    Log    ${TEST MESSAGE}
    ${ordinary}[${KEYWORD STATUS}] =    Set Variable    value
