*** Test Cases ***
Outside of loop
    Exit For Loop
    Exit For Loop If    $condition
    Continue For Loop
    Continue For Loop If    $condition

In FOR
    FOR    ${var}    IN  1  2
        BREAK
        IF    $condition
            BREAK
        END
        CONTINUE
        IF    $condition
            CONTINUE
        END
    END

In While
    WHILE    $condition
        BREAK
        IF    $condition
            BREAK  # comment
        END
        CONTINUE  # comment
        IF    $condition
            CONTINUE
        END
    END


*** Keywords ***
Nested Loops
    FOR    ${var}    IN    @{LIST}
        WHILE    $condition
            CONTINUE
            IF    $var > 10
                BREAK
            END
        END
    END

Multiline Statements
    FOR    ${var}    IN    @{LIST}
        IF    $condition
            BREAK
        END
    END

Missing Condition
    FOR    ${var}    IN    @{LIST}
        Exit For Loop If
    END
