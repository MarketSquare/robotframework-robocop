*** Keywords ***
Resource Keyword
    FOR    ${a}    IN    1
        IF    $a
            WHILE    $a
                TRY
                    IF    $a
                        Log    deep
                    END
                EXCEPT
                    Log    failed
                END
            END
        END
    END
