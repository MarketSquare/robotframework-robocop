*** Test Cases ***
Outside of loop
    BREAK
    CONTINUE
    Exit For Loop
    Exit For Loop If
    Continue For Loop
    Continue For Loop If    $condition

In FOR
    FOR    ${var}    IN  1  2
        BREAK
        CONTINUE
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
        CONTINUE
        BREAK
        IF    $condition
            BREAK
        END
        CONTINUE
        IF    $condition
            CONTINUE
        END
    END

*** Keywords ***
Outside of loop
    BREAK
    CONTINUE
    Exit For Loop
    Exit For Loop If    $condition
    Continue For Loop
    Continue For Loop If    $condition

In FOR
    FOR    ${var}    IN  1  2
        BREAK  # comment
        CONTINUE  # comment
        BREAK  # comment
        IF    $condition
            BREAK  # comment
        END
        CONTINUE  # comment
        IF    $condition
            CONTINUE  # comment
        END
    END

In While
    WHILE    $condition
        BREAK
        CONTINUE
        BREAK
        IF    $condition
            BREAK
        END
        CONTINUE
        IF    $condition
            CONTINUE
        END
    END

Multiline Statements
    FOR    ${var}    IN    @{LIST}
        IF    $condition
            BREAK
        END
    END
