*** Keywords ***
No Control Flow
    Log    one
    Log    two

Flat Branches
    IF    $status == 200
        Log    ok
    ELSE IF    $status == 404
        Log    not found
    ELSE IF    $status == 500
        Log    error
    ELSE
        Log    other
    END

At Limit
    FOR    ${a}    IN    1
        IF    $a
            FOR    ${b}    IN    1
                WHILE    $b    limit=3
                    Log    ${b}
                END
            END
        END
    END

Too Deep
    FOR    ${order}    IN    @{orders}
        IF    $order.pending
            TRY
                IF    $order.priority
                    WHILE    $order.open
                        Escalate    ${order}
                    END
                END
            EXCEPT
                Log    failed
            END
        END
    END

Deeper Inside Reported Block Is Not Reported Again
    FOR    ${a}    IN    1
        FOR    ${b}    IN    1
            FOR    ${c}    IN    1
                FOR    ${d}    IN    1
                    FOR    ${e}    IN    1
                        FOR    ${f}    IN    1
                            Log    deep
                        END
                    END
                END
            END
        END
    END

Two Deep Blocks
    IF    $a
        IF    $b
            IF    $c
                IF    $d
                    IF    $e
                        Log    first
                    END
                END
            END
        END
    END
    FOR    ${x}    IN    1
        WHILE    $x
            TRY
                WHILE    $y
                    IF    $z
                        Log    second
                    END
                END
            FINALLY
                Log    cleanup
            END
        END
    END

Else If Branch Nesting Is Not Cumulative
    IF    $first
        Log    first
    ELSE IF    $second
        FOR    ${i}    IN    1
            IF    $i
                TRY
                    Log    third
                EXCEPT
                    Log    caught
                END
            END
        END
    ELSE
        Log    other
    END

Except And Try Else Branches
    TRY
        Risky
    EXCEPT    A
        FOR    ${i}    IN    1
            IF    $i
                WHILE    $i
                    Log    in except
                END
            END
        END
    ELSE
        IF    $a
            IF    $b
                IF    $c
                    Log    in try else
                END
            END
        END
    FINALLY
        Cleanup
    END

Inline If Is A Guard Clause
    FOR    ${a}    IN    1
        IF    $a
            FOR    ${b}    IN    1
                IF    $b
                    IF    $b    CONTINUE
                    IF    $b    Log    ${b}    ELSE    Log    other
                    ${x} =    IF    $b    Set Variable    1    ELSE    Set Variable    2
                END
            END
        END
    END

Inline If Split Over Lines
    FOR    ${a}    IN    1
        IF    $a
            IF    $b
                IF    $c
                    Log    in block
                END
                IF    $a
                ...    Log    split
                ...    ELSE
                ...    Log    inline
            END
        END
    END

Conditional Keywords Do Not Nest
    FOR    ${a}    IN    1
        IF    $a
            IF    $b
                Run Keyword If    $c    Log    one    ELSE    Log    two
                Skip If    $c
                Return From Keyword If    $c
                Run Keyword And Return If    $c    Log    ${c}
            END
        END
    END

Sequential Blocks Do Not Accumulate
    IF    $a
        Log    a
    END
    IF    $b
        Log    b
    END
    IF    $c
        Log    c
    END
    FOR    ${i}    IN    1
        Log    ${i}
    END
    WHILE    $d
        Log    d
    END
    TRY
        Log    e
    EXCEPT
        Log    f
    END
