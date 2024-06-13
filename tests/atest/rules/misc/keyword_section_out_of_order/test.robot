*** Settings ***
Documentation  doc


*** Test Cases ***
Test
    [Documentation]  doc
    [Tags]  sometag
    Correct Keyword    arg


*** Keywords ***
Correct Keyword
    [Documentation]  this is doc
    [Tags]    xd
    [Arguments]    ${argument1}
    [Timeout]    30
    No Operation
    No Operation
    Fail
    [Teardown]    Log    Cleaning

Documentation After Tags
    [Tags]    xd
    [Documentation]  this is doc
    No Operation

Tags After Arguments
    [Documentation]  this is doc
    [Arguments]    ${argument1}
    [Tags]    xd
    Fail

Arguments After Timeout
    [Documentation]  this is doc
    [Timeout]    30
    [Arguments]    ${argument1}
    No Operation

Teardown After Teardown
    [Documentation]  this is doc
    No Operation
    [Teardown]    Log    Cleaning
    No Operation
