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

Test With Tags
    [Tags]    dummy
    Log    2


*** Keywords ***
Keyword
    [Documentation]  this is doc
    No Operation
    Pass
    No Operation
    Fail

Keyword With Tags
    [Tags]    tag
    No Operation

Keyword With Empty Tags
    [Tags]
    No Operation
