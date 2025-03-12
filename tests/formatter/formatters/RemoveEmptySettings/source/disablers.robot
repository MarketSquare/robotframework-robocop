*** Settings ***
Documentation  # robocop: fmt: off
# robocop: fmt: off
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
    [Setup]  # robocop: fmt: off
    [Template]    #  comment    and    comment  # robocop: fmt: off
    [Tags]    tag
    Keyword
# robocop: fmt: off
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
    [Return]  # robocop: fmt: off
# robocop: fmt: off
Keyword 2
    [Arguments]
    Keyword
    [Return]    stuff
