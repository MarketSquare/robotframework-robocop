*** Settings ***
Documentation  doc


*** Test Cases ***
Test
    [Documentation]  doc
    [Tags]  sometag
    Pass
    Keyword
    One More

Test 2
    [Documentation]  doc
    [Tags]  othertag  sometag
    Pass
    Keyword
    One More


*** Keywords ***
Keyword
    [Documentation]  doc
    [Tags]      tag
    No Operation
    Pass
    No Operation
    Fail

Keyword 2
    [Documentation]  doc
    [Tags]      tag     tag2
    No Operation
    Pass
    No Operation
    Fail
