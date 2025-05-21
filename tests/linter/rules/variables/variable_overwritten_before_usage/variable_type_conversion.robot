*** Variables ***
# Simple type.
${version: float}         7.3
# Parameterized type.
${CRITICAL: list[int]}    [3278, 5368, 5417]
# With @{list} variables the type specified the item type.
@{HIGH: int}              4173    5334    5386    5387
@{HIGH low: int}              4173    5334    5386    5387
# With @{dict} variables the type specified the value type.
&{DATes: date}            rc1=2025-05-08    final=2025-05-15
# Alternative syntax to specify both key and value types.
&{NUMBERS: int=float}     1=2.3    4=5.6


*** Test Cases ***
VAR syntax
    # The VAR syntax supports types the same way as the Variables section
    VAR    ${number: int}      42
    VAR    ${number2: int}      42
    VAR    ${number}      42
    Log    ${number2}
    VAR    ${number2}      42

Assignment
    [Tags]    robot:continue-on-failure
    # In simple cases the VAR syntax is more convenient.
    ${number: int} =    Set Variable    42
    ${number: str}    Convert To Integer    42

    # or even convert to list
    ${variable: list[str]}    Set Variable    42    43
    Should Be Equal    ${variable}    ${42}

    # In this example conversion is more useful.
    ${match}    ${number} =    Should Match Regexp    RF 7.3    ^RF (\\d+\\.\\d+)$

Keyword arguments
    # Argument conversion with user keywords is very convenient!
    Move    10    down    slow=no
    # Conversion handles validation automatically. This usage fails.
    Move    10    invalid

Embedded argumemts
    # Also embedded arguments can be converted.
    Move 3.14 meters

Other
    Blocks

*** Keywords ***
Move
    [Arguments]    ${distance: int}    ${direction: Literal["UP", "DOWN"]}    ${slow: bool}=True
    Should Be Equal    ${distance}     ${10}
    Should Be Equal    ${direction}    DOWN
    Should Be Equal    ${slow}         ${False}

Move ${distance: int | float} meters
    Should Be Equal    ${distance}     ${3.14}

Return Variable
    [Arguments]    ${variable}
    RETURN    ${variable}

Blocks
    # 'var: int' will be unused, since FOR does not support var type conversion
    FOR    ${var: int}    IN    @{list_of_strings}
        Type Should Be    ${var}    int
    END
