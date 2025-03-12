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
    No Operation
    Pass
    No Operation
    Fail

 # Special case

Disabled Rule
    # robocop: off=missing-doc-keyword
    Disablers Should Check Inside Node For Disabler
