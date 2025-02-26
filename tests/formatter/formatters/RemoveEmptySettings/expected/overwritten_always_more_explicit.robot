*** Settings ***
Metadata    doc=1
Test Setup    Keyword
Test Teardown    Keyword
Test Timeout    1 min
Default Tags    tag


*** Test Cases ***
Test
    [Tags]    tag
    Keyword

Test 2
    [Setup]    Keyword
    [Template]    Keyword
    [Timeout]    1min
    Keyword

Test 3
    Keyword



*** Keywords ***
Keyword
    [Arguments]    ${arg}
    Keyword

Keyword 2
    Keyword
    [Return]    stuff
