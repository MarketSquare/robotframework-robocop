*** Settings ***
Documentation    Test Suite

*** Test Cases ***
Correct
    [Documentation]    This is test Documentation
    [Tags]    tag1    tag2
    Keyword1
    [Teardown]    Teardown

Keyword After Teardown
    [Documentation]    This is test Documentation
    [Tags]    tag1    tag2
    [Teardown]    Log    abc
    Keyword1

Documentation After Tags
    [Tags]    tag1    tag2
    [Documentation]    This is test Documentation
    Keyword1

Tags After Timeout
    [Documentation]    This is test Documentation
    [Timeout]    30
    [Tags]    MyTag
    Keyword1

Timeout After Setup
    [Documentation]    This is test Documentation
    [Setup]    Log    Setting up
    [Timeout]    30
    Keyword1

Setup After Template
    [Documentation]    This is test Documentation
    [Template]    Do Stuff
    [Setup]    Log    Setting up
    a    b

Template After Teardown
    [Documentation]    This is test Documentation
    [Teardown]    Teardown
    [Template]    Do Stuff
    a    b


*** Keywords ***
Keyword1
    No Operation

Teardown
    No Operation

Do Stuff
    [Arguments]    ${arg1}    ${arg2}
    Log    ${arg1}
    Log    ${arg2}
