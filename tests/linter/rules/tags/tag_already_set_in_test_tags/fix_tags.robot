*** Settings ***
Force Tags    common    shared


*** Test Cases ***
Only Redundant Tag
    [Tags]    common
    Step

Redundant And Own Tags
    [Tags]    common    own
    Step

Redundant Tag With Comment
    [Tags]    own    common    # comment
    Step

Only Redundant Tag With Comment
    [Tags]    common    # comment
    Step

Multiline Tags
    [Tags]    own
    ...    common
    ...    shared    own2
    Step

No Redundant Tags
    [Tags]    own
    Step