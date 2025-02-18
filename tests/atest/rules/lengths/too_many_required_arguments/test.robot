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
    No Operation
    Pass
    No Operation
    Fail

Keyword With Allowed Number Of Arguments
    [Documentation]  A keyword
    [Arguments]     ${arg1}   ${arg2}  ${arg3}   ${arg4}   ${arg5}
    No Operation
    No Operation

Keyword With Too Many optional Arguments
    [Documentation]  this is doc
    [Arguments]  ${var1}=optional  ${var2}=optional  ${var3}=optional  ${var4}=optional  ${var5}=optional  ${var6}=optional
    No Operation
    Pass
    No Operation
    Fail
