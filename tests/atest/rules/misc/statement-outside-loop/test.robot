*** Test Cases ***
Test
    Continue For Loop
    FOR    ${var}    IN RANGE    10
        Keyword 2
        Exit For Loop
        Continue For Loop
        CONTINUE
        BREAK
        Exit For Loop If    $condition
        Continuefor_loopIf    $condition
    END
    BuiltIn.Exit For Loop
    CONTINUE
    BREAK
    Exit For Loop If    $condition
    Continuefor_loopIf    $condition

Test 2
    Exit For Loop
    Continue For Loop
    CONTINUE
    BREAK


*** Keywords ***
Keyword
    Continue For Loop
    CONTINUE
    BREAK
    FOR    ${var}    IN RANGE    10
        Keyword 2
        FOR    ${var}    IN RANGE    10
            CONTINUE
            BREAK
        END
        Keyword
        Exit For Loop
        BREAK
    END
    Keyword
    Exit For Loop

Keyword 2
    Keyword
    Exit For Loop
    Continue For Loop
    IF    $condition
        CONTINUE
    END
    BREAK
    IF    $condition    Exit For Loop If    $condition
    Continuefor_loopIf    $condition

WHILE loop
    WHILE    $condition
        Exit For Loop
        TRY
            Continue For Loop
        EXCEPT
            BREAK
        END
        BREAK    value
        CONTINUE
    END
    TRY
        Continue For Loop
    EXCEPT
        BREAK
    END
