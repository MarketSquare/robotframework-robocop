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

Disabled Rule
    # robocop: off=missing-doc-test-case
    Disablers Should Check Inside Node For Disabler


*** Keywords ***
Keyword
    [Documentation]  this is doc
    No Operation
    Pass
    No Operation
    Fail
