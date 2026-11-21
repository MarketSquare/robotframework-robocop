*** Test Cases ***
Flat Test
    Log    one
    IF    $a
        Log    two
    ELSE IF    $b
        Log    three
    END

At Limit
    FOR    ${a}    IN    1
        IF    $a
            WHILE    $a
                Log    ${a}
            END
        END
    END

Too Deep
    FOR    ${a}    IN    1
        IF    $a
            WHILE    $a
                TRY
                    Log    ${a}
                EXCEPT
                    IF    $b
                        Log    deeper
                    END
                END
            END
        END
    END

Inline If Guards
    FOR    ${a}    IN    1
        IF    $a
            WHILE    $a
                IF    $a    BREAK
                Run Keyword If    $a    Log    ${a}
            END
        END
    END

*** Test Cases ***
Second Section Test Case
    TRY
        FOR    ${a}    IN    1
            IF    $a
                TRY
                    Log    ${a}
                END
            END
        END
    END
