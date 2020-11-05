*** Settings ***
Documentation  doc
Library    MyLib
Library    OtherLib
Resource  some_resource.robot
Library    MyLib


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
