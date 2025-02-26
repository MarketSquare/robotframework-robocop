*** Settings ***
Documentation  # robotidy: off
# robotidy: off
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
    [Setup]  # robotidy: off
    [Template]    #  comment    and    comment  # robotidy: off
    [Tags]    tag
    Keyword
# robotidy: off
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
    [Return]  # robotidy: off
# robotidy: off
Keyword 2
    [Arguments]
    Keyword
    [Return]    stuff
