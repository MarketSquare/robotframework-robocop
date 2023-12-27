*** Settings ***
Documentation  doc


*** Test Cases ***
Test
    [Documentation]  doc
    [Tags]  sometag
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

Only VAR
    VAR    ${variable}
    VAR    ${variable}
    VAR    ${variable}

Short Keyword
    Keyword

Empty Keyword

Keyword
