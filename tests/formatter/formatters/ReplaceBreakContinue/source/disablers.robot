*** Test Cases ***
Outside of loop
    BREAK  # robocop: fmt: off
    CONTINUE  # robocop: fmt: off
    Exit For Loop  # robocop: fmt: off
    Exit For Loop If  # robocop: fmt: off
    Continue For Loop  # robocop: fmt: off
    Continue For Loop If    $condition  # robocop: fmt: off

In FOR
    FOR    ${var}    IN  1  2
        # robocop: fmt: off
        BREAK
        CONTINUE
        Exit For Loop
        Exit For Loop If    $condition
        Continue For Loop
        Continue For Loop If    $condition
    END

In While
    # robocop: fmt: off
    WHILE    $condition
        BREAK
        CONTINUE
        Exit For Loop
        Exit For Loop If    $condition
        Continue For Loop
        Continue For Loop If    $condition
    END

*** Keywords ***
# robocop: fmt: off
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
