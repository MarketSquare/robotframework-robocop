*** Test Cases ***
Outside of loop
    BREAK  # robotidy: off
    CONTINUE  # robotidy: off
    Exit For Loop  # robotidy: off
    Exit For Loop If  # robotidy: off
    Continue For Loop  # robotidy: off
    Continue For Loop If    $condition  # robotidy: off

In FOR
    FOR    ${var}    IN  1  2
        # robotidy: off
        BREAK
        CONTINUE
        Exit For Loop
        Exit For Loop If    $condition
        Continue For Loop
        Continue For Loop If    $condition
    END

In While
    # robotidy: off
    WHILE    $condition
        BREAK
        CONTINUE
        Exit For Loop
        Exit For Loop If    $condition
        Continue For Loop
        Continue For Loop If    $condition
    END

*** Keywords ***
# robotidy: off
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
