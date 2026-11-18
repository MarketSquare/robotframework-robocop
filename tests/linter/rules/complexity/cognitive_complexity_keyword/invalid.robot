*** Keywords ***
Broken Keyword
    IF    $a
        Log    x
    ELSE
    EXCEPT    x
    END
    END

Unclosed Loop
    FOR    ${i}    IN    a
        IF    $i    Log    x

Complex After Errors
    FOR    ${i}    IN RANGE    3
        IF    $i > 0
            IF    $i > 1
                IF    $i > 2
                    IF    $i > 3
                        IF    $i > 4
                            Log    deep
                        END
                    END
                END
            END
        END
    END
