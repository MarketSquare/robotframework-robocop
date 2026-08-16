*** Settings ***
Force Tags    tag    other


*** Test Cases ***
Duplicated Tags
    [Tags]    tag    dummy
    Step

Duplicated Tags With Comment
    [Tags]    tag    # comment
    Step

Multiline Duplicated Tags
    [Tags]    tag    other
    ...    own
    Step


*** Keywords ***
Duplicated Tags In Documentation
    [Documentation]    Tags:    tag,    other,    tag
    Step