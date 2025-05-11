*** Keywords ***
Move
    [Arguments]    ${distance: int}    ${direction: Literal["UP", "DOWN"]}    ${slow: bool}=True
    No Operation

Move ${distance: int | float} meters
    No Operation
