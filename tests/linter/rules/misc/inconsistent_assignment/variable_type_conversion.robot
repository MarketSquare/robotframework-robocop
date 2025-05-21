*** Test Cases ***
Assignment
    [Tags]    robot:continue-on-failure
    # In simple cases the VAR syntax is more convenient.
    ${number: int}    Set Variable    42
    Should Be Equal    ${number}    ${42}

    # we can also convert other keywords output
    ${number: str}    Convert To Integer    42
    Should Be Equal    ${number}    ${42}

    # or even convert to list
    ${variable: list[str]}    Set Variable    42    43
    Should Be Equal    ${variable}    ${42}

    # In this example conversion is more useful.
    ${match}    ${version: float} =    Should Match Regexp    RF 7.3    ^RF (\\d+\\.\\d+)$
    Should Be Equal    ${match}      RF 7.3
    Should Be Equal    ${version}    ${7.3}
