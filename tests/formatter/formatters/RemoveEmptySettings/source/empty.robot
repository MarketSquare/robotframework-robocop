*** Settings ***
Documentation
Suite Setup
Metadata
Metadata    doc=1
Test Setup
Test Teardown
Test Template
Test Timeout
Force Tags
Default Tags
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
