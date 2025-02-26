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
Duplicated Keyword
    [Documentation]  this is doc
    No Operation
    Pass
    No Operation
    Fail

Just Keyword
    No Operation

Duplicated Keyword
    No Operation
