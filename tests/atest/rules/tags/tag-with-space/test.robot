*** Settings ***
Documentation  doc
Force Tags    with space
Default Tags  with space


*** Test Cases ***
Test
    [Documentation]  doc
    [Tags]  some tag
    Pass
    Keyword
    One More


*** Keywords ***
Keyword
    [Documentation]  this is doc
    ...              Tags:  space tag
    No Operation
    Pass
    No Operation
    Fail
