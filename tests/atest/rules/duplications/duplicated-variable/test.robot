*** Settings ***
Documentation  doc


*** Variables ***
${v_ar}       10
${other_var}  20
${V AR}       a


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
