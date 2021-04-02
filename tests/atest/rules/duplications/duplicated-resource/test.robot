*** Settings ***
Documentation  doc
Resource  resource.robot
Resource  other_file.robot
Resource  resource.robot


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
    Fail
