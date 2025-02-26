*** Settings ***
Documentation  doc
Force Tags  sometag  othertag


*** Test Cases ***
Test
    [Documentation]  doc
    Pass
    Keyword
    One More


*** Keywords ***
Keyword
    [Documentation]  this is doc
    [Tags]  sometag  anothertag
    No Operation
    Pass
    No Operation
    Fail
