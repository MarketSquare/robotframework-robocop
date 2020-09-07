*** Settings ***
Documentation  Suite for duplicated test cases and keywords
Library   PythonLibrary  1
Library   PythonLibrary  1
Resource  resource.robot
Library   PythonLibrary  2
Library   PythonLibrary
Resource  resource2.robot
Resource  resource.robot
Metadata  This is some metadata
Metadata  This is some metadata
...       over more than one line
Metadata  This is some metadata
Metadata  ${var}
Variables  file.robot
Variables  file2.robot
Variables  file.robot
Metadata  ${var}

*** Variables ***
${var}  smth
${var}  smth2

${var1}  1
@{var}  a  b
^{var}  3


*** Test Cases ***
First test case
    [Documentation]  First
    Log  First
    Log  First
    For    ${i}    IN RANGE    10
        log    ${i}
    end
    For    item    in    list

Second test case
    [Documentation]  Second
    Log  Second
    Log  Second

First test case
    [Documentation]  Third
    Log  Third
    Log  Third


*** Keywords ***
First_Keyword
    [Documentation]  First
    Pass
    Fail

Second Keyword
    [Documentation]  Second
    Pass
    Fail

First keyword
    [Documentation]  Third
    Pass
    Fail
