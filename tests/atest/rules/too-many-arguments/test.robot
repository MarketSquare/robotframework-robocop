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
    [Documentation]  this is doc
    [Arguments]  ${var1}  @{var2}  ${var3}  ${var4}  ${var5}  ${var6}
    No Operation
    Pass
    No Operation
    Fail
