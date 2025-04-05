*** Settings ***
Keyword Tags    tag3


*** Keywords ***
Keyword
    [Tags]  tag    tag2    tag3
    No Operation

Keyword 2
    [Tags]  tag   tag2    tag3
    No Operation
