*** Settings ***
Documentation    This is suite doc


*** Variables ***
${var} =    1
${var2}=    2
${var3}     3


*** Test Cases ***
Test without keyword
    ${var}  ${var1}

Test
    ${var}    Keyword


*** Keywords ***
Keyword Without Assignments
    Keyword
    Log  ${1}

Keyword With One Assignment
    ${var} =    Keyword

Keyword With Multiple Assignments
    ${var}    ${var2}    Keyword

Keyword With Multiline Keyword
    ${var}    ${var}=    Keyword
    ...    ${arg}
    ...    ${1}
