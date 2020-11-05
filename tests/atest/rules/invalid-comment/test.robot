*** Settings ***
Documentation  doc

 # here comment is fine
*** Test Cases ***
Test
    [Documentation]  doc
    [Tags]  sometag
    Pass
    Keyword
    One More
 # this is invalid comment - should start from first cell

*** Keywords ***
Keyword
    [Documentation]  this is doc
    No Operation
    Pass
    No Operation
    Fail
