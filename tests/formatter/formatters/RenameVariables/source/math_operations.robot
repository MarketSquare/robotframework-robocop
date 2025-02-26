*** Test Cases ***
Simple math operations
    ${i}    Set Variable    ${0}
    Log    ${i+1}

Global Value
    Log    ${i-1}

Invalid syntax
    ${i}    Set Variable    ${0}
    ${y}    Set Variable    ${1}
    Log    ${i+y+1}
