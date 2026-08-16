*** Settings ***
Keyword Tags    common    shared


*** Keywords ***
Only Redundant Tag
    Step

Redundant And Own Tags
    [Tags]    own
    Step

Multiline Tags
    [Tags]    own
    ...    own2
    Step