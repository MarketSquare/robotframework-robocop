*** Settings ***
Documentation  doc
Variables  variables.py
Variables  other.robot
Variables  variables.py

Variables  other.py    arg1
Variables  other.py    arg2
Variables  other1.py    arg1
Variables  other1.py    arg1
Variables  vars.yaml    arg1
Variables  vars.yaml
...    arg1
Variables  vars2.yaml
Variables  vars2.yaml
Variables  variables
Variables  variables    arg    arg2


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
