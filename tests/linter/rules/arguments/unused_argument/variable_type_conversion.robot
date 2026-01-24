*** Keywords ***
Move
    [Arguments]    ${distance: int}    ${direction: Literal["UP", "DOWN"]}    ${slow: bool}=True
    No Operation

Move ${distance: int | float} meters
    No Operation

Move and use arguments
    [Arguments]    ${distance: int}    ${direction: Literal["UP", "DOWN"]}    ${slow: bool}=True
    Log    ${distance}
    Keyword Call    ${direction} and ${slow}

Move ${distance: int | float} meters and use arguments
    Log    ${distance}
