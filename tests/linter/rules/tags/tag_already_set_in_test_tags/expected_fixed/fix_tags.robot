*** Settings ***
Force Tags    common    shared


*** Test Cases ***
Only Redundant Tag
    Step

Redundant And Own Tags
    [Tags]    own
    Step

Redundant Tag With Comment
    [Tags]    own    # comment
    Step

Only Redundant Tag With Comment
    # comment
    Step

Multiline Tags
    [Tags]    own
    ...    own2
    Step

No Redundant Tags
    [Tags]    own
    Step