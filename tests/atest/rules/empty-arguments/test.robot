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
Keyword Without Arguments
    [Documentation]  this is doc
    [Arguments]
    No Operation
    Pass
    No Operation
    Fail

Keyword With Arguments
    [Arguments]  ${var}
    No Operation
