*** Settings ***
Documentation  doc


*** Test Cases ***
Test
    [Tags]  sometag
    Pass
    Keyword
    One More

Test With Doc
    [Documentation]  Some documentation
    My Keyword

*** Keywords ***
Keyword
    [Documentation]  this is doc
    No Operation
    Pass
    No Operation
    Fail
