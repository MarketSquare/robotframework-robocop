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
        Exit For Loop
        Exit For Loop If    $condition
        Continue For Loop
        Continue For Loop If    $condition
    END

In While
    WHILE    $condition
        BREAK
        CONTINUE
        Exit For Loop
        Exit For Loop If    $condition
        Continue For Loop
        Continue For Loop If    $condition
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
        Exit For Loop  # comment
        Exit For Loop If    $condition  # comment
        Continue For Loop  # comment
        Continue For Loop If    $condition  # comment
    END

In While
    WHILE    $condition
        BREAK
        CONTINUE
        Exit For Loop
        Exit For Loop If    $condition
        Continue For Loop
        Continue For Loop If    $condition
    END

Multiline Statements
    FOR    ${var}    IN    @{LIST}
        Exit For Loop If
        ...    $condition
    END
