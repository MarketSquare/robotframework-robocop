*** Settings ***
Documentation  doc
Force Tags    with space
Default Tags  with space    ${var with space}    ${var} space


*** Test Cases ***
Test
    [Documentation]  doc
    [Tags]  some tag    ${var with space}    ${var} space
    Pass
    Keyword
    One More


*** Keywords ***
Keyword
    [Documentation]  this is doc
    ...              Tags: space tag,${var with space}tag, ${var} space
    No Operation
    Pass
    No Operation
    Fail
