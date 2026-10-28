*** Test Cases ***
Test
    Set Local Variable    ${variable}    0
    Log    ${variable}
    Log    ${VARIABLE}
    Log    ${var_iable}


*** Keywords ***
Keyword With Set Local Variable
    Set Local Variable    ${variable}    0
    Log    ${varia ble}
    Set Local Variable    ${nested_${variable}}    0
    Log    ${NESTED_${VARIABLE}}

Keyword With Invalid Set Local Variable
    Set Local Variable    invalid    0
    Set Local Variable    $escaped    0
    Set Local Variable
    ...
    ...    previous arg is empty now
    Log    ${invalid}
