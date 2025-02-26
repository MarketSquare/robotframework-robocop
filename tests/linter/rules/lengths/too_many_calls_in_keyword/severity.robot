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
    No Operation
    No Operation
    No Operation
    No Operation
    No Operation
    FOR  ${var}  IN RANGE  10
        No Operation
        No Operation
    END

Keyword 2
    [Documentation]  this is doc
    No Operation
    Pass
    No Operation
    Fail
    No Operation
    No Operation
