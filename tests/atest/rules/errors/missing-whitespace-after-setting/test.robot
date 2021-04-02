*** Settings ***
Documentation  doc


*** Test Cases ***
Test
    [Documentation] doc
    [Tags]  sometag
    Pass
    Keyword
    One More


*** Keywords ***
Keyword
    [Documentation]  this is doc
    [Arguments] ${var}
    No Operation
    Pass
    No Operation
    Fail
