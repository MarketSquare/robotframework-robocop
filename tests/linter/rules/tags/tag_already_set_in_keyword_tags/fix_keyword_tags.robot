*** Settings ***
Keyword Tags    common    shared


*** Keywords ***
Only Redundant Tag
    [Tags]    common
    Step

Redundant And Own Tags
    [Tags]    common    own
    Step

Multiline Tags
    [Tags]    own
    ...    common
    ...    shared    own2
    Step