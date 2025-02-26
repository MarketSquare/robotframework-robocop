*** Settings ***
Metadata    doc=1


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
