*** Settings ***
Documentation  doc


*** Test Cases ***
Test
    [Documentation]  doc
    [Tags]  sometag
    Pass
    Keyword
    Keyword
    Keyword
    Keyword
    Keyword
    Keyword
    Keyword
    Keyword
    Keyword
    Keyword
    VAR    ${variable}    value    scope=GLOBAL
    One More


*** Keywords ***
Keyword
    [Documentation]  this is doc
    No Operation
    Pass
    No Operation
    Fail
