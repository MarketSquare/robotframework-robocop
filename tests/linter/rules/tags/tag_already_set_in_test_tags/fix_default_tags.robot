*** Settings ***
Default Tags    default
Force Tags    common


*** Test Cases ***
Only Redundant Tag
    [Tags]    common
    Step

Redundant And Own Tags
    [Tags]    common    own
    Step