*** Test Cases ***
Outside of loop
    Exit For Loop
    Exit For Loop If    $condition
    Continue For Loop
    Continue For Loop If    $condition

In FOR
    FOR    ${var}    IN  1  2
        Exit For Loop
        Exit For Loop If    $condition
        Continue For Loop
        Continue For Loop If    $condition
    END

In While
    WHILE    $condition
        BuiltIn.Exit For Loop
        Exit For Loop If    $condition  # comment
        Continue For Loop  # comment
        Continue For Loop If    $condition
    END


*** Keywords ***
Nested Loops
    FOR    ${var}    IN    @{LIST}
        WHILE    $condition
            Continue For Loop
            Exit For Loop If    $var > 10
        END
    END

Multiline Statements
    FOR    ${var}    IN    @{LIST}
        Exit For Loop If
        ...    $condition
    END

Missing Condition
    FOR    ${var}    IN    @{LIST}
        Exit For Loop If
    END
