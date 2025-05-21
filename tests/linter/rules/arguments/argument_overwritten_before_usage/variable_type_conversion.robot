*** Keywords ***
Move
    [Arguments]    ${distance: int}    ${direction: Literal["UP", "DOWN"]}    ${slow: bool}=True
    VAR    ${distance}     ${10}
    VAR    ${direction}    DOWN
    VAR    ${slow}         ${False}

Move ${distance: int | float} meters
    VAR    ${distance}     ${3.14}
