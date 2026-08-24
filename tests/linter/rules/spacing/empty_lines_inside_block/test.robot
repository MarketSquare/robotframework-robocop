*** Test Cases ***
Clean
    FOR    ${var}    IN    1    2
        Keyword Call
    END

For Loop
    FOR    ${var}    IN    1    2

        Keyword Call

    END

While Loop
    WHILE    $condition

        Log    message

    END

If Else
    IF    $condition

        Log    1

    ELSE

        Log    2

    END

Try Except
    TRY

        Log    1

    EXCEPT    error

        Log    2

    FINALLY

        Log    3

    END

Multiple Empty Lines
    FOR    ${var}    IN    1    2


        Keyword Call


    END

Nested
    FOR    ${var}    IN    1    2
        WHILE    $condition

            Log    nested

        END
    END
