*** Settings ***
Documentation    This is suite doc


*** Test Cases ***
Test
    [Documentation]   doc
    ${var}    Keyword


*** Keywords ***
Keyword With One Assignment
    [Documentation]  doc
    ${var}    Keyword
    ${var1}    ${var2}    Keyword

Keyword With Used Assignment
    [Documentation]  Gold test
    ${var}    Keyword
    Log     ${var}

Keyword With Different Format Variable
    [Documentation]  Gold test
    @{var test}    Keyword
    Log     ${VAR_Test}
