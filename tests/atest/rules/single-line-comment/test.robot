*** Settings ***
Documentation  doc


*** Test Cases ***
Test
    [Documentation]  doc
    [Tags]  sometag
    Pass
    Keyword # valid comment
    One More


*** Keywords ***
Keyword
    [Documentation]  this is doc
    # This will create a warning
    Pass
    No Operation
    Fail
