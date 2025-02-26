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
Keyword With Too Many Arguments
    [Documentation]  this is doc
    [Arguments]  ${var1}  @{var2}  ${var3}  ${var4}  ${var5}  ${var6}
    No Operation
    Pass
    No Operation
    Fail

Keyword With Too Many Arguments In Multi Lines
    [Documentation]  this is doc
    [Arguments]  ${var1}  @{var2}
    ...  ${var3}  ${var4}
    ...  ${var5}  ${var6}
    ...  ${var}
    No Operation
    Pass
    No Operation
    Fail

Keyword With Allowed Number Of Arguments
    [Documentation]  A keyword
    [Arguments]     ${arg1}=1   ${arg2}=2  ${arg3}=3   ${arg4}=4   ${arg5}=5
    No Operation
    No Operation
