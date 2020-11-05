*** Settings ***
Documentation  doc


*** Test Cases ***
Test
    [Documentation]  doc
    [Tags]  sometag
    Pass
    Keyword # valid comment
    One More


*** Keywords ***
Keyword
    [Documentation]  this is doc
    No Operation  #invalid comment
    Pass
    No Operation
    Fail
