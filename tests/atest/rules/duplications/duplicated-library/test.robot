*** Settings ***
Documentation  doc
Library    MyLib
Library    OtherLib
Library
Resource  some_resource.robot
Library    MyLib
Library    MyLib    arg
Library    MyLib    arg
Library    MyLib  WITH NAME    MyLib2
Library    MyLib  AS    MyLib3
Library    MyLib  AS    MyLib2
Library    MyLib    argument    AS    MyLib2


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
