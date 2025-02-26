*** Keywords ***
Keyword With Inline IF
    Log    ${global}
    ${GLOBAL}    IF    $condition    Keyword
    Log    ${global}
