*** Settings ***
Documentation  doc


*** Test Cases ***
Test
    [Documentation]  doc
    [Tags]  sometag
    Pass
    Keyword
    One More

# fixme: this whole section
*** Keywords ***
Keyword
    [Documentation]  this is doc
    No Operation  # todo: do something
    Pass
    No Operation
    Fail
