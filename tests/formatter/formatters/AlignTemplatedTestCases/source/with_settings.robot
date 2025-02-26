*** Settings ***
Test Template    Dummy

*** Test Cases ***
Test1    ARG1
    [Tags]    sanity
    [Documentation]  Validate Test1
Test2    ARG2
    [Tags]    smoke
    [Documentation]  Validate Test2
Test3    ARG3
    [Tags]    valid
    [Documentation]  Validate Test3
Test4    ARG4
    [Tags]    sanity
    [Documentation]  Validate Test4