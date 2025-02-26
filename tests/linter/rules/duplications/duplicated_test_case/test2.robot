*** Settings ***
Documentation  doc


*** Test Cases ***
Test 1
    [Documentation]  doc
    [Tags]  sometag
    Pass
    Keyword
    One More

test1
    No Operation

Te s t_1
    No Operation


*** Keywords ***
Keyword
    [Documentation]  this is doc
    No Operation
    Pass
    No Operation
    Fail
