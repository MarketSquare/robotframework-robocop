*** Settings ***
Documentation  doc
Test Tags  sometag  othertag


*** Test Cases ***
Test
    [Documentation]  doc
    [Tags]  sometag  anothertag
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
