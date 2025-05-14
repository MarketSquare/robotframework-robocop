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
    # robocop: fmt: off
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
