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
    [Setup]    Log    Preparing
    No Operation
    No Operation
    Fail
    [Teardown]    Log    Cleaning

Timeout After Setup
    [Documentation]  this is doc
    [Setup]    Log    Preparing
    [Timeout]    30
    No Operation

Setup After Keyword
    [Documentation]  this is doc
    No Operation
    [Setup]    Log    Preparing
    Log    Test

