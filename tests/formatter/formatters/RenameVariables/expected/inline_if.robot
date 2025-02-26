*** Keywords ***
Keyword With Inline IF
    Log    ${GLOBAL}
    ${global}    IF    $condition    Keyword
    Log    ${global}
