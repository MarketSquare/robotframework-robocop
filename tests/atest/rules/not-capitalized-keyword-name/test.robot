*** Settings ***
Documentation  doc


*** Test Cases ***
Test
    [Documentation]  doc
    [Tags]  sometag
    pass
    Keyword
    One More


*** Keywords ***
keyword
    [Documentation]  this is doc
    No Operation
    Pass
    No Operation
    Fail
