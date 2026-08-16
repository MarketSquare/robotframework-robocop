*** Settings ***
Force Tags    tag    TAG    t ag    other


*** Test Cases ***
Duplicated Tags
    [Tags]    tag    dummy    TAG    t a g
    Step

Duplicated Tags With Comment
    [Tags]    tag    tag    # comment
    Step

Multiline Duplicated Tags
    [Tags]    tag    other
    ...    TAG
    ...    t ag    own
    Step


*** Keywords ***
Duplicated Tags In Documentation
    [Documentation]    Tags:    tag,    other,    tag
    Step