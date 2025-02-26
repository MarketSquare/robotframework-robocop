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
    [Return]    ${var}
    Fail

Keyword
    [Documentation]  this is doc
    No Operation
    Pass
    No Operation
    [Return]    ${var}

Last teardown - [Return]
    [Setup]   Setup
    ${arg}    Step
    [Return]  ${arg}
    [Teardown]    Teardown

Last teardown - RETURN
    [Setup]   Setup
    ${arg}    Step
    RETURN  ${arg}
    [Teardown]    Teardown
