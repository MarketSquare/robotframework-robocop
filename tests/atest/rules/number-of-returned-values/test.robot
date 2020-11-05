*** Settings ***
Documentation  doc


*** Test Cases ***
Test
    [Documentation]  doc
    [Tags]  sometag
    Pass
    Keyword
    One More


*** Keywords ***
Keyword
    [Documentation]  this is doc
    No Operation
    Pass
    No Operation
    Fail
    [Return]    ${var}  2  4  4  5

Keyword 2
    Return From Keyword  ${var}  2  4  4  5

Keyword 3
    Return From Keyword If    ${condition}==${True}    ${var}  2  4  4  5
