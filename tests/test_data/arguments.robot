*** Settings ***
Documentation  Test data for rule checking if number of arguments is not exceeded


*** Test Cases ***
Simple Test Case
    [Documentation]  A simple test case
    Keyword With Too Many Arguments
    Keyword With Too Many Arguments  1  2  3  4  5  6
    Keyword With Allowed Number Of Arguments  1  2  3  4  5


*** Keywords ***
Keyword With Too Many Arguments
    [Documentation]  A keyword
    [Arguments]     ${arg1}=1   ${arg2}=2  ${arg3}=3   ${arg4}=4   ${arg5}=5   ${arg6}=6
    No Operation
    No Operation

Keyword With Allowed Number Of Arguments
    [Documentation]  A keyword
    [Arguments]     ${arg1}=1   ${arg2}=2  ${arg3}=3   ${arg4}=4   ${arg5}=5
    No Operation
    No Operation
