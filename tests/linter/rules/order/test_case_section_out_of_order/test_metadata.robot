*** Test Cases ***
Correct
    [Documentation]    This is test Documentation
    [Metadata]    Owner    Team Robot
    [Metadata]    Ticket    RF-4409
    [Tags]    tag1    tag2
    Keyword1
    [Teardown]    Teardown

Metadata After Tags
    [Documentation]    This is test Documentation
    [Tags]    tag1    tag2
    [Metadata]    Owner    Team Robot
    Keyword1

Metadata After Keyword
    [Documentation]    This is test Documentation
    Keyword1
    [Metadata]    Owner    Team Robot


*** Keywords ***
Keyword1
    No Operation

Teardown
    No Operation
