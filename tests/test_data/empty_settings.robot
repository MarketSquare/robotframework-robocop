*** Settings ***
Metadata  not empty
Metadata
Documentation
Force Tags
Default Tags
Library
Resource
Variables
Suite Setup
Suite Teardown
Test Setup
Test Teardown
Test Timeout


*** Test Cases ***
Test
    [Documentation]
    [Setup]
    [Timeout]
    Pass
    Fail
    [Teardown]


*** Keywords ***
Keyword
    [Arguments]
    [Documentation]
    [Timeout]
    Pass
    Pass
    [Teardown]