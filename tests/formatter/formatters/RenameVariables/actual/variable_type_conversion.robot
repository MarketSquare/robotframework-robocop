*** Variables ***
# Simple type.
${VERSION: float}         7.3
# Parameterized type.
${CRITICAL: list[int]}    [3278, 5368, 5417]
# With @{list} variables the type specified the item type.
@{HIGH: int}              4173    5334    5386    5387
@{HIGH_LOW: int}              4173    5334    5386    5387
# With @{dict} variables the type specified the value type.
&{DA_TES: date}            rc1=2025-05-08    final=2025-05-15
# Alternative syntax to specify both key and value types.
&{NUMBERS: int=float}     1=2.3    4=5.6


*** Test Cases ***
Variables section
    # Validate above variables using the inline Python evaluation syntax.
    # This syntax is much more complicated than the syntax used above!
    Should Be Equal    ${VERSION}       ${{7.3}}
    Should Be Equal    ${CRITICAL}      ${{[3278, 5368, 5417]}}
    Should Be Equal    ${HIGH}          ${{[4173, 5334, 5386, 5387]}}
    Should Be Equal    ${DATES}         ${{{'rc1': datetime.date(2025, 5, 8), 'final': datetime.date(2025, 5, 15)}}}
    Should Be Equal    ${NUMBERS}       ${{{1: 2.3, 4: 5.6}}}

VAR syntax
    # The VAR syntax supports types the same way as the Variables section
    VAR    ${number: int}      42
    Should Be Equal    ${number}    ${42}

Assignment
    [Tags]    robot:continue-on-failure
    # In simple cases the VAR syntax is more convenient.
    ${number: int} =    Set Variable    42
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
    FOR    ${var: int}    IN    @{LIST_OF_STRINGS}
        Type Should Be    ${var}    int
    END
