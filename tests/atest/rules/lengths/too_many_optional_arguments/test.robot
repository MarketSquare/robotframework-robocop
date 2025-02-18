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
    [Arguments]  ${var1}=optional  ${var2}=optional  ${var3}=optional  ${var4}=optional  ${var5}=optional  ${var6}=optional  ${var7}=optional  ${var8}=optional  ${var9}=optional  ${var10}=optional  ${var11}=optional
    No Operation
    Pass
    No Operation
    Fail

Keyword With Too Many Arguments In Multi Lines
    [Documentation]  this is doc
    [Arguments]  ${var1}=optional  ${var2}=optional
    ...  ${var3}=optional  ${var4}=optional
    ...  ${var5}=optional  ${var6}=optional
    ...  ${var7}=optional  ${var8}=optional
    ...  ${var9}=optional  ${var10}=optional
    ...  ${var11}=optional
    No Operation
    Pass
    No Operation
    Fail

Keyword With Allowed Number Of Arguments
    [Documentation]  A keyword
    [Arguments]     ${arg1}=optional   ${arg2}=optional  ${arg3}=optional   ${arg4}=optional   ${arg5}=optional  ${var6}=optional  ${var7}=optional  ${var8}=optional  ${var9}=optional  ${var10}=optional
    No Operation
    No Operation
