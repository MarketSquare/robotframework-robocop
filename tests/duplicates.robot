*** Settings ***
Documentation  Suite for duplicated test cases and keywords
Library   PythonLibrary  1
Library   PythonLibrary  1
Resource  resource.robot
Library   PythonLibrary  2
Library   PythonLibrary
Resource  resource2.robot
Resource  resource.robot

*** Variables ***
${var}  smth
${var}  smth2

${var1}  1
@{var}  a  b


*** Test Cases ***
First test case
    [Documentation]  First
    Log  First
    Log  First

Second test case
    [Documentation]  Second
    Log  Second
    Log  Second

First test case
    [Documentation]  Third
    Log  Third
    Log  Third


*** Keywords ***
First Keyword
    [Documentation]  First
    Pass
    Fail

Second Keyword
    [Documentation]  Second
    Pass
    Fail

First Keyword
    [Documentation]  Third
    Pass
    Fail
