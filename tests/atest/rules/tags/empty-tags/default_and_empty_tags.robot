*** Settings ***
Documentation  doc
Default Tags  tag  othertag

*** Test Cases ***
Test
    [Documentation]  doc
    [Tags]
    Pass
    Keyword
    One More


*** Keywords ***
Keyword
    [Documentation]  this is doc
    No Operation
    Pass
    No Operation
    Fail
