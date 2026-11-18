*** Test Cases ***
Simple Test
    Log    hello

Flat Test
    IF    $a == 1    Log    1
    IF    $a == 2    Log    2
    IF    $a == 3    Log    3
    IF    $a == 4    Log    4
    IF    $a == 5    Log    5
    IF    $a == 6    Log    6
    IF    $a == 7    Log    7
    IF    $a == 8    Log    8
    IF    $a == 9    Log    9
    IF    $a == 10    Log    10

Medium Nested Test
    FOR    ${i}    IN    @{items}
        IF    $i > 0
            IF    $i > 1 and $ok
                Log    x
            ELSE
                IF    $i == 0    Log    y
            END
        END
    END

Deeply Nested Test
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


*** Keywords ***
Simple Keyword
    Log    hello

Moderate Keyword
    FOR    ${i}    IN    @{items}
        IF    $i > 0
            IF    $i > 1 and $ok
                Log    x
            ELSE
                IF    $i == 0    Log    y
            END
        END
    END

Nested Control Flow
    [Arguments]    ${items}    ${mode}
    FOR    ${item}    IN    @{items}
        IF    $mode == 'a'
            IF    $item > 10
                Log    big
            ELSE IF    $item > 5
                Log    medium
            ELSE
                Log    small
            END
        ELSE IF    $mode == 'b' and $item != 0
            WHILE    $item > 0    limit=10
                ${item}=    Evaluate    $item - 1
                IF    $item == 3    BREAK
            END
        END
    END
    TRY
        Risky Keyword
    EXCEPT    ValueError*    type=glob
        Log    value error
    EXCEPT    AS    ${err}
        Log    ${err}
    FINALLY
        Log    done
    END

Suppressed Keyword    # robocop: off
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
