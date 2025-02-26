*** Keywords ***
IF block
    IF    $condition
        Keyword
    ELSE IF    $other_value
        Consecutive

        Two Empty Lines
    ELSE
        IF    $condition
            Keyword
        END
    END

FOR and WHILE blocks
    FOR    ${value}    IN RANGE  10
        WHILE    $value < 5
            Keyword

            Keyword
        END
    END

TRY EXCEPT
    TRY
        ${arg}    Keyword
    EXCEPT
         Keyword

         Consecutive
    ELSE
        Keyword With
        ...    ${arg}
        ...    break
    FINALLY
        Trailing
    END
