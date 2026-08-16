*** Settings ***
Default Tags    default
Force Tags    common


*** Test Cases ***
Only Redundant Tag
    [Tags]    NONE
    Step

Redundant And Own Tags
    [Tags]    own
    Step