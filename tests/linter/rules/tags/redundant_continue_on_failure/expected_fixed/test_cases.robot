*** Test Cases ***
Simple wrapper
    [Tags]    robot:continue-on-failure
    Should Be Equal    ${value}    expected    # inline comment

Recursive tag and BuiltIn prefix
    [Tags]    ROBOT:RECURSIVE-CONTINUE-ON-FAILURE
    Log    message

Multiline wrapper with comments
    [Tags]    robot:continue-on-failure
    # wrapper comment
    # before wrapped keyword
    Should Be Equal
    ...    ${actual}    ${expected}    # argument comment

Wrapper around nested run keyword
    [Tags]    robot:continue-on-failure
    Run Keyword If    ${condition}    First Keyword    ELSE    Other Keyword

Nested wrapper on one line
    [Tags]    robot:recursive-continue-on-failure
    Run Keyword If    ${condition}    Inner Keyword    argument

Nested multiline wrapper
    [Tags]    robot:continue-on-failure
    Run Keyword If    ${condition}
    ...    Inner Keyword    argument

Nested multiline wrapper after outer arguments
    [Tags]    robot:continue-on-failure
    Run Keyword If    ${condition}    # keep this comment
    ...    Inner Keyword

Multiple nested wrappers
    [Tags]    robot:continue-on-failure
    Run Keywords    First Keyword    AND    Second Keyword

Nested multiline wrapper after outer arguments without comment
    [Tags]    robot:continue-on-failure
    Run Keyword If    ${condition}
    ...    Inner Keyword

Assigned wrapper is ignored
    [Tags]    robot:continue-on-failure
    ${result}=    Run Keyword And Continue On Failure    Keyword Returning Value

Wrapper nested in assigned call is ignored
    [Tags]    robot:continue-on-failure
    ${result}=    Run Keyword If    ${condition}    Run Keyword And Continue On Failure    Keyword Returning Value
