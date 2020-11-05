*** Settings ***
Documentation  doc


*** Test Cases ***
Test
    [Documentation]  doc
    [Tags]  sometag
    Pass
    Keyword
    One More  ${var}
    ... ${var2}


*** Keywords ***
Keyword
    [Documentation]  this is doc
    ... and new line
    No Operation
    Pass
    No Operation
    Fail
