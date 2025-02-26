*** Settings ***
Metadata    doc=1
Test Setup    Keyword
Test Teardown    Keyword
Test Timeout    1 min
Default Tags    tag


*** Test Cases ***
Test
    [Setup]    NONE
    [Tags]    tag
    Keyword

Test 2
    [Setup]    Keyword
    [Template]    Keyword
    [Timeout]    1min
    [Tags]    NONE
    Keyword
    [Teardown]    NONE

Test 3
    [Timeout]    NONE
    Keyword



*** Keywords ***
Keyword
    [Arguments]    ${arg}
    Keyword

Keyword 2
    Keyword
    [Return]    stuff
