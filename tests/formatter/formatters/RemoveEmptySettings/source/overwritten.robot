*** Settings ***
Documentation
Suite Setup
Metadata
Metadata    doc=1
Test Setup    Keyword
Test Teardown    Keyword
Test Template
Test Timeout    1 min
Force Tags
Default Tags    tag
Library
Resource
Variables


*** Test Cases ***
Test
    [Setup]
    [Template]    #  comment    and    comment
    [Tags]    tag
    Keyword

Test 2
    [Setup]    Keyword
    [Template]    Keyword
    [Timeout]    1min
    [Tags]
    Keyword
    [Teardown]

Test 3
    [Timeout]
    Keyword



*** Keywords ***
Keyword
    [Arguments]    ${arg}
    Keyword
    [Return]

Keyword 2
    [Arguments]
    Keyword
    [Return]    stuff
